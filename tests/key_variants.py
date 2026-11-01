"""
tests/key_variants.py -- the one table of the ways one name or one text can be written differently, that every
key of common/common_helpers/triples_io.py and common/common_helpers/text_match.py must even out (or keep apart),
and the annotation page's own keys too (helpers/annotator/page.html, looseKey and isDescribes, run in headless
Chrome over the same table by tests/test_keys.py).

Each family: (a, b, same): whether the two must get the same key. Near misses (same: False) are as important as
the matches: they prove a key doesn't merge what differs.
"""

SOFT_HYPHEN, ZWSP, ZWNJ, ZWJ, WORD_JOINER, BOM, NBSP, NARROW_NBSP = ("­", "​", "‌", "‍", "⁠",
                                                                     "﻿", " ", " ")

#: Component classes (entity classes and predicates): triples_io.component_class_key, and the page's looseKey.
#: Case, spacing, punctuation, "_" and "-", invisible format characters, Unicode variants (full-width, ligatures,
#: composed or not), accents and case folding (ß, İ, final sigma) are evened out; letters of any script are kept,
#: and so are digits.
NAMES = [
    ("Instrument", "INSTRUMENT", True),
    ("Instrument", "instrument", True),
    ("PhysicalQuantity", "physical quantity", True),
    ("PhysicalQuantity", "Physical_Quantity", True),
    ("HAS_PART", "HASPART", True),
    ("HAS_PART", "has-part", True),
    ("HAS_PART", "has part.", True),
    ("Instrument", "Ｉnstrument", True),                  # a full-width I
    ("Instrument", f"Instru{SOFT_HYPHEN}ment", True),
    ("Instrument", f"Instru{ZWSP}ment", True),
    ("Instrument", f"Instru{ZWNJ}ment", True),
    ("Instrument", f"Instru{ZWJ}ment", True),
    ("Instrument", f"Instru{WORD_JOINER}ment", True),
    ("Instrument", f"{BOM}Instrument", True),
    ("Instrument", f"Instrument{NBSP}", True),
    ("Instrument", f"Instrument{NARROW_NBSP}", True),
    ("Résolution", "Resolution", True),                        # an accent
    ("Résolution", "Résolution", True),             # composed and decomposed
    ("Straße", "STRASSE", True),                               # ß
    ("İnstrument", "instrument", True),                        # a dotted capital I
    ("ΔT", "δt", True),                                        # Greek letters are letters
    ("ΟΔΟΣ", "οδος", True),                                    # a final sigma
    ("ﬁle", "file", True),                                     # a ligature
    ("Level2", "LEVEL_2", True),
    # near misses
    ("ΔT", "T", False),                                        # a Greek letter is never dropped
    ("Δ", "", False),
    ("Ünit", "nit", False),
    ("Level2", "Level3", False),
    ("Instrument", "Instruments", False),
    ("ABOARD", "ON_BOARD", False),
    ("Dataset", "Datasets", False),
]

#: Component instances: text_match.instance_key (and norm_text). Case, spacing (NBSP too), quote marks, dashes,
#: invisible format characters, full-width letters, composed and decomposed accents, edge punctuation, a leading
#: "the/a/an", and quantities written another way are evened out; digits, accents and words are kept.
INSTANCES = [
    ("MODIS", "modis", True),
    ("Terra­Aqua", "TerraAqua", True),
    (f"Terra{ZWSP}Aqua", "TerraAqua", True),
    (f"Terra{WORD_JOINER}Aqua", "TerraAqua", True),
    (f"{BOM}Aqua", "Aqua", True),
    (f"Aqua{NBSP}satellite", "Aqua satellite", True),
    ("“Aqua”", "Aqua", True),                        # curly quotes
    ("Earth’s", "Earth's", True),
    ("Level–2", "Level-2", True),                         # an en dash
    ("ＭODIS", "MODIS", True),                             # a full-width M
    ("Résolution", "Résolution", True),
    ("the Aqua satellite.", "Aqua satellite", True),
    ("1 km", "1000 m", True),
    ("1 kilometer (km)", "1 km", True),
    ("500m", "500 m", True),
    # near misses
    ("Level-2", "Level 3", False),
    ("1 km", "10 km", False),
    ("Résolution", "Resolution", False),                       # an instance keeps its accents (they are its words)
    ("Aqua", "Aquarius", False),
    ("MODIS Terra", "MODIS", False),
]

#: Same fact (triples_io.triple_key: the key the ground truth's repeat check, 050's and 060's duplicate check and
#: 070's exact pairs share): subject and object instances by instance_key, the predicate by component_class_key, and
#: a symmetric predicate's subject and object either way round.
FACTS = [
    (("MODIS", "ABOARD", "Aqua"), ("modis", "aboard", "Aqua."), True),
    (("MODIS", "HAS_PART", "Aqua"), ("MODIS", "HASPART", "Aqua"), True),
    (("MODIS", "IS_ABOARD", "Aqua"), ("MODIS", "is aboard", "Aqua"), True),
    (("X", "HAS_SPATIAL_RESOLUTION", "1 km"), ("X", "HAS_SPATIAL_RESOLUTION", "1000 m"), True),
    (("Terra", "ALSO_KNOWN_AS", "EOS AM-1"), ("EOS AM-1", "ALSO_KNOWN_AS", "Terra"), True),
    (("Terra­Aqua", "ABOARD", "X"), ("TerraAqua", "ABOARD", "X"), True),
    # near misses
    (("MODIS", "ABOARD", "Aqua"), ("Aqua", "ABOARD", "MODIS"), False),         # not symmetric
    (("X", "HAS_SPATIAL_RESOLUTION", "1 km"), ("X", "HAS_SPATIAL_RESOLUTION", "10 km"), False),
    (("MODIS", "ABOARD", "Aqua"), ("MODIS", "ON_BOARD", "Aqua"), False),
]

#: The describes triple (triples_io.is_describes, and the page's isDescribes): its subject class and predicate by
#: component_class_key.
DESCRIBES = [
    (("CatalogEntry", "DESCRIBES"), True),
    (("catalog_entry", "describes"), True),
    (("Catalog Entry", "Describes."), True),
    ((f"Catalog{SOFT_HYPHEN}Entry", "DESCRIBES"), True),
    (("CATALOGENTRY", f"DE{ZWSP}SCRIBES"), True),
    # near misses
    (("CatalogEntry", "DESCRIBED"), False),
    (("Catalog", "DESCRIBES"), False),
    (("Dataset", "DESCRIBES"), False),
]

#: Looked up in a text (text_match.Text.contains): (text, needle, found).
IN_TEXT = [
    ("data from Terra­Aqua satellites", "TerraAqua", True),
    (f"data from Terra{ZWSP}Aqua", "TerraAqua satellite", False),
    (f"MODIS{NBSP}aboard Aqua", "MODIS aboard Aqua", True),
    ("the “Aqua” satellite", "Aqua satellite", True),
    (f"Aqua{WORD_JOINER}rius", "Aqua", False),                 # a word joiner joins: "Aquarius"
    ("Salinity from Aquarius", "Aqua", False),
]

#: The passages of a source text (triples_io.passages, rule 17 of "Writing a classed triple"): the joins a person or
#: a model writes, each read as the join " … ".
PASSAGES = [
    ("MODIS aboard Aqua … since 2002", ["MODIS aboard Aqua", "since 2002"]),
    ("MODIS aboard Aqua ... since 2002", ["MODIS aboard Aqua", "since 2002"]),
    ("MODIS aboard Aqua…since 2002", ["MODIS aboard Aqua", "since 2002"]),
    ("MODIS aboard Aqua...since 2002", ["MODIS aboard Aqua", "since 2002"]),
    ("MODIS aboard Aqua …since 2002", ["MODIS aboard Aqua", "since 2002"]),
    ("MODIS aboard Aqua", ["MODIS aboard Aqua"]),
    ("… MODIS aboard Aqua …", ["MODIS aboard Aqua"]),
]
