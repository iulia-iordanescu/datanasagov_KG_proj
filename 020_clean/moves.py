"""
moves.py -- the main moves of 020_clean, as called by 020_clean.py.

    stage 1  (here)  load_raw          code: check extra_text_fields, read every 010 batch file; drop records
                                       with no id, and later copies of a repeated id
    stage 2  (here)  keep_fields       code: one record per catalog entry, each field under its own key, with its origin
    stage 3  (here)  clean_text        code: HTML in the text fields → plain text, nothing lost (note_cleaning.py)
    stage 4  (here)  join_maintainers  code: one name per maintainer, however it was spelled (maintainers.py)
    -        (here)  results           writes records.jsonl; the report

Terms are as defined in docs/terminology.md.

One line of records.jsonl, shortened:

    {"id": "a1b2…", "name": "modis-aqua-…", "title": "MODIS/Aqua …", "notes": "…",
     "maintainer": "Kristan Morgan", "maintainer_as_harvested": "KRISTAN MORGAN",
     "organization": "NASA", "tags": ["earth science"], "formats": ["HDF"],
     "license": "…", "url": "…", "metadata_created": "…", "metadata_modified": "…",
     "_cleaning": {"title": "parsed", "notes": "parsed"},
     "_origin": ["010_harvest/batch_00000.json#a1b2…"]}

Apart from records with no id and later copies of a repeated id, every
record is kept, even one with no title or notes: the graph needs every
catalog entry, and its structured fields still hold facts.
"""
from __future__ import annotations

import collections
import json
from dataclasses import dataclass, field
from pathlib import Path

import maintainers
import note_cleaning
from common.audit import ORIGIN_FIELD, check_origins, log, origin
from common.files import write_jsonl
from common.records_io import TEXT_FIELDS
from common.report import cell
from common.step import Results, input_files

OUTPUT_NAME = "records.jsonl"
CLEANING_FIELD = "_cleaning"         # which method cleaned each text field
SHOW = 20                            # items listed in the report before "…"
#: Text fields that are one line by nature: every run of line breaks and
#: spaces inside becomes one space. (notes keeps its line breaks: they
#: separate paragraphs.) 3,283 of 36,375 titles had one on 2026-09-27, e.g.
#: "ROSETTA-ORBITER 67P RSI 1/2/3" + a line break + 37 spaces + "COMET ESCORT …".
ONE_LINE_FIELDS = ("title",)

#: TEXT_FIELDS (from common/records_io.py, which every later step reads
#: records with): the free-text fields every record gets, always cleaned and
#: saved. The extra_text_fields setting can only add to them.

#: The other fields keep_fields writes. An extra text field can't take one of
#: these names, or it would overwrite that field.
STRUCTURED_FIELDS = ("id", "name", "maintainer", "maintainer_as_harvested", "organization",
                     "tags", "formats", "license", "url", "metadata_created",
                     "metadata_modified", CLEANING_FIELD, ORIGIN_FIELD)


@dataclass
class Catalog:
    """The records as they move through the step, and what each move found."""
    raw: list = field(default_factory=list)          # (batch file, raw CKAN record)
    records: list = field(default_factory=list)      # the cleaned records, in batch order
    files: int = 0
    read: int = 0
    dropped_no_id: list = field(default_factory=list)   # {"file", "position", "name", "title"}
    repeats: list = field(default_factory=list)         # ids whose later copies were dropped
    text_fields: tuple = ()                             # TEXT_FIELDS, then the extra ones
    missing_field: collections.Counter = field(default_factory=collections.Counter)
    tiers: dict = field(default_factory=dict)            # {field: Counter of methods}
    with_html: collections.Counter = field(default_factory=collections.Counter)  # {field: values with tags or escapes}
    fallbacks: list = field(default_factory=list)       # {"id", "field", "method"}
    no_text: int = 0                                    # records with every text field empty
    made_one_line: collections.Counter = field(default_factory=collections.Counter)  # {field: values joined into one line}
    joined: bool = False
    maintainers_before: int = 0
    maintainers_after: int = 0
    joins: list = field(default_factory=list)


# --------------------------------------------------------------------------

def _text_fields(settings: dict) -> tuple:
    """TEXT_FIELDS plus the extra_text_fields setting. Checked before any file
    is read, so a bad setting stops the step at once."""
    extra = settings["extra_text_fields"].split()
    clashes = [name for name in extra if name in STRUCTURED_FIELDS]
    if clashes:
        raise ValueError(f"extra_text_fields names {', '.join(clashes)}, which 020 already writes "
                         f"as a field of its own; a text field of that name would overwrite it.")
    # title and notes named again are harmless: each field is listed once.
    return tuple(dict.fromkeys(TEXT_FIELDS + tuple(extra)))


def load_raw(inputs: dict, settings: dict) -> Catalog:
    catalog = Catalog(text_fields=_text_fields(settings))
    seen = set()
    files = input_files(inputs["batches"])
    catalog.files = len(files)
    for path in files:
        batch = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(batch, dict) or "records" not in batch:
            raise ValueError(f"{path.name} is in the old batch format (a bare list, with no "
                             f"request block). Rerun 010_harvest to fetch it again.")
        for position, raw in enumerate(batch["records"]):
            catalog.read += 1
            rid = str(raw.get("id") or "").strip()
            if not rid:
                # With no id, the record is named by where it sits and what it says.
                dropped = {"file": path.name, "position": position,
                           "name": raw.get("name"), "title": raw.get("title")}
                catalog.dropped_no_id.append(dropped)
                log.debug(f"{path.name}#{position}: no id; dropped "
                          f"(name {dropped['name']!r}, title {dropped['title']!r})")
                continue
            if rid in seen:
                # A change to the catalog during the harvest can shift CKAN's
                # pages (see 010), so a record can arrive twice. The first
                # copy is kept.
                catalog.repeats.append(rid)
                log.debug(f"{path.name}#{position}: id {rid} seen before; later copy dropped")
                continue
            seen.add(rid)
            catalog.raw.append((path, raw))
    log.info(f"  read {catalog.read:,} records from {catalog.files} batch files")
    return catalog


def _text(value) -> str | None:
    return value if value is None or isinstance(value, str) else str(value)


def keep_fields(catalog: Catalog) -> Catalog:

    for path, raw in catalog.raw:
        rid = str(raw["id"]).strip()
        record = {"id": rid, "name": raw.get("name")}
        for name in catalog.text_fields:
            if name not in raw:
                catalog.missing_field[name] += 1
            record[name] = _text(raw.get(name))            # cleaned by clean_text
        record["maintainer"] = maintainers.as_harvested(raw.get("maintainer"))  # joined later
        record["maintainer_as_harvested"] = str(raw.get("maintainer") or "")
        record["organization"] = (raw.get("organization") or {}).get("title")
        record["tags"] = [t["name"] for t in raw.get("tags") or []
                          if isinstance(t, dict) and t.get("name")]
        formats = [str(r.get("format") or "").strip() for r in raw.get("resources") or []
                   if isinstance(r, dict)]
        record["formats"] = list(dict.fromkeys(f for f in formats if f))
        record["license"] = raw.get("license_title")
        record["url"] = raw.get("url")
        record["metadata_created"] = raw.get("metadata_created")
        record["metadata_modified"] = raw.get("metadata_modified")
        record[CLEANING_FIELD] = {}                          # filled by clean_text
        record[ORIGIN_FIELD] = [origin(path, rid)]
        catalog.records.append(record)
    catalog.raw = []                                         # no longer needed
    return catalog


def clean_text(catalog: Catalog) -> Catalog:
    # The library checks itself before it is trusted with the catalog: its
    # regression cases must pass in the environment it runs in.
    note_cleaning.selftest()
    log.debug("note_cleaning self-test passed")

    catalog.tiers = {name: collections.Counter() for name in catalog.text_fields}
    for record in catalog.records:
        methods = {}
        for name in catalog.text_fields:
            note = note_cleaning.clean_note(record[name])
            record[name] = note.text
            if name in ONE_LINE_FIELDS:
                one_line = " ".join(note.text.split())
                catalog.made_one_line[name] += one_line != note.text
                record[name] = one_line
            methods[name] = note.tier
            catalog.tiers[name][note.tier] += 1
            catalog.with_html[name] += note.had_markup
            if note.needs_review:
                catalog.fallbacks.append({"id": record["id"], "field": name, "method": note.tier})
                log.debug(f"{record['id']}: {name} cleaned by the {note.tier} method")
        record[CLEANING_FIELD] = methods
        if not any(record[name].strip() for name in catalog.text_fields):
            catalog.no_text += 1
    return catalog


def join_maintainers(catalog: Catalog, settings: dict) -> Catalog:
    # Like the cleaning library, the joining rules check themselves first.
    maintainers.selftest()
    log.debug("maintainers self-test passed")

    names = [r["maintainer"] for r in catalog.records]
    catalog.maintainers_before = len(set(names))
    catalog.joined = settings["join_maintainers"]
    if catalog.joined:
        mapping, catalog.joins = maintainers.join(names)
        for record in catalog.records:
            record["maintainer"] = mapping[record["maintainer"]]
    catalog.maintainers_after = len({r["maintainer"] for r in catalog.records})
    log.info(f"  {catalog.maintainers_before:,} maintainer spellings, "
             f"{catalog.maintainers_after:,} maintainers after joining them")
    return catalog


# --------------------------------------------------------------------------

def _listed(items: list) -> str:
    shown = ", ".join(f"`{i}`" for i in items[:SHOW])
    return shown + (f" … ({len(items) - SHOW:,} more)" if len(items) > SHOW else "")


def results(catalog: Catalog, output: Path) -> Results:
    path = output / OUTPUT_NAME
    write_jsonl(path, catalog.records)
    written = len(catalog.records)
    log.info(f"  wrote {written:,} records to {OUTPUT_NAME}")

    warnings = []
    if catalog.dropped_no_id:
        n = len(catalog.dropped_no_id)
        warnings.append(f"{n:,} record{'s' if n != 1 else ''} {'have' if n != 1 else 'has'} "
                        f"no id and {'were' if n != 1 else 'was'} dropped; every later step "
                        f"tells records apart by id. All are listed in the report under "
                        f"What this run worked on, and in the log.")
    uncleaned = sum(c[note_cleaning.TIER_SOURCE] for c in catalog.tiers.values())
    if uncleaned:
        warnings.append(f"{uncleaned:,} text values could not be cleaned without losing content, "
                        f"so they were kept as decoded, markup included. Their ids are listed "
                        f"in the report under Cleaning.")
    if catalog.joined and catalog.maintainers_after == 1 and written > 1:
        warnings.append("Every record has the same maintainer, so 040 would learn the schema "
                        "from one maintainer only.")
    missing = check_origins(catalog.records, "records")
    if missing:
        warnings.append(missing)

    lines = [
        "### What this run worked on", "",
        "| Records | |", "|---|---:|",
        f"| Read from {catalog.files} batch files | {catalog.read:,} |",
        f"| Dropped: no id | {len(catalog.dropped_no_id):,} |",
        f"| Dropped: later copy of a repeated id | {len(catalog.repeats):,} |",
        f"| **Written** | **{written:,}** |",
        f"| … of which with no text in {' or '.join(catalog.text_fields)} (kept) | {catalog.no_text:,} |",
        "",
    ]
    if catalog.dropped_no_id:
        lines += ["Records dropped for having no id (all of them):", "",
                  "| Batch file | Position | Name | Title |", "|---|---:|---|---|"]
        for d in catalog.dropped_no_id:
            lines.append(f"| {d['file']} | {d['position']} | {cell(d['name'])} | {cell(d['title'])} |")
        lines.append("")
    if catalog.repeats:
        lines += [f"Repeated ids (first copy kept): {_listed(catalog.repeats)}", ""]

    methods = [note_cleaning.TIER_PARSED, note_cleaning.TIER_CONSERVATIVE, note_cleaning.TIER_SOURCE]
    lines += ["### Cleaning", "",
              "*With HTML* counts the values that had HTML tags or escapes to remove; every "
              "other value only had its whitespace tidied. Each value is checked after "
              "cleaning: every word, number and URL of the input must still be there. "
              "*parsed* is the normal method (and includes every value without HTML); "
              "*conservative* is a cruder fallback; *source* means the value is kept as "
              "decoded, markup included.", "",
              "| Field | Values | With HTML | " + " | ".join(methods) + " | Missing from the record |",
              "|---|" + "---:|" * (len(methods) + 3)]
    for name in catalog.text_fields:
        counts = catalog.tiers.get(name, {})
        lines.append(f"| `{name}` | {sum(counts.values()):,} | {catalog.with_html[name]:,} | "
                     + " | ".join(f"{counts.get(m, 0):,}" for m in methods)
                     + f" | {catalog.missing_field.get(name, 0):,} |")
    lines.append("")
    for name in ONE_LINE_FIELDS:
        if name in catalog.text_fields:
            lines += [f"`{name}` is one line by nature: {catalog.made_one_line[name]:,} values had line breaks "
                      f"or runs of spaces inside, each now one space.", ""]
    if catalog.fallbacks:
        shown = [f"{f['id']} ({f['field']}, {f['method']})" for f in catalog.fallbacks]
        lines += [f"Values that needed a fallback method, worth a look: {_listed(shown)}", ""]

    lines += ["### Maintainers", ""]
    if catalog.joined:
        lines += [f"{catalog.maintainers_before:,} maintainer spellings (spaces tidied), "
                  f"**{catalog.maintainers_after:,}** maintainers after joining them "
                  f"({len(catalog.joins):,} maintainers were written more than one way).", ""]
        if catalog.joins:
            lines += ["| Joined as | Spellings | Records |", "|---|---|---:|"]
            for j in catalog.joins[:SHOW]:
                spellings = " · ".join(s.replace("|", "\\|") for s in j["spellings"])
                lines.append(f"| {j['name']} | {spellings} | {j['records']:,} |")
            if len(catalog.joins) > SHOW:
                lines.append(f"| … {len(catalog.joins) - SHOW:,} more | | |")
            lines.append("")
    else:
        lines += [f"{catalog.maintainers_after:,} maintainers, spellings left as harvested "
                  f"(`join_maintainers` is off).", ""]
    ranked = collections.Counter(r["maintainer"] for r in catalog.records).most_common(10)
    lines += ["Largest maintainers:", "", "| Maintainer | Records |", "|---|---:|"]
    lines += [f"| {name.replace('|', chr(92) + '|')} | {n:,} |" for name, n in ranked]

    return Results(
        files=[path],
        headline={"records written": written, "maintainers": catalog.maintainers_after},
        details="\n".join(lines),
        warnings=warnings,
    )
