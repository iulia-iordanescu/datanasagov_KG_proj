"""
helpers/models.py -- the AI models a service lists for your account, and which of them you may use.

    py helpers/models.py                                  LiteLLM's list (free; the default service)
    py helpers/models.py --service asksage                Ask Sage's list (free)

Free: listing is not a model call. Being listed doesn't guarantee access:
Ask Sage may list a model and still refuse it. (LiteLLM lists only the
models your key may use, but a model may still fail, e.g. on a setting it
doesn't accept.) To use one, give the service and the model's name to a
step's settings, e.g.

    py 050_annotate/run.py --service asksage --model <name>

To find out which models you may use, before choosing one:

    py helpers/models.py --try <name> <name>                       these models (names from the list)
    py helpers/models.py --try all                                 every listed model

Each try is the same one-line test call a step makes first: one tiny paid
call per model. It asks before paying, then prints, for each model, usable
or refused, with the service's reason. Needs the NASA network and your key
in .env (docs/running_on_nasa_laptop.md). Not a pipeline step: it writes
nothing.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common import llm


def try_models(wanted: list, listed: list, service: str = llm.SERVICE) -> list:
    """[(name, usable, why)] for the models wanted ("all": every listed one), through the service, after asking
    before paying."""
    names = listed if wanted == ["all"] else list(dict.fromkeys(wanted))
    unlisted = [n for n in names if n not in listed]
    if unlisted:
        print(f"\nNot in {llm.SERVICES[service]}'s list, so probably misspelled or not offered (tried anyway): {', '.join(unlisted)}")
    llm.confirm(f"Try {len(names)} model(s), one tiny test call each ({len(names)} paid call(s))? Press Enter to go "
                f"ahead, or anything else to cancel.")
    out = []
    for name in names:
        usable, why = llm.try_model(name, service)
        print(f"  {name}: {'usable' if usable else 'refused: ' + why}")
        out.append((name, usable, why))
    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="py helpers/models.py",
                                description="The AI models a service lists for your account; with --try, which of "
                                            "them you may use.")
    p.add_argument("--service", default=llm.SERVICE, choices=list(llm.SERVICES),
                   help=f"the service whose models to list or try (default: {llm.SERVICE})")
    p.add_argument("--try", dest="wanted", nargs="+", metavar="NAME",
                   help="model names to try (one tiny paid call each), or all")
    args = p.parse_args()
    names = llm.list_models(args.service)
    where = llm.SERVICES[args.service]
    if not args.wanted:
        print(f"{where} lists {len(names)} model(s) for your account (listed doesn't mean usable; "
              f"`py helpers/models.py --service {args.service} --try <name> ...` finds out):")
        for name in names:
            print(f"  {name}{'   <- the default' if name == llm.MODEL else ''}")
        if args.service == llm.SERVICE and llm.MODEL not in names:
            print(f"\nThe default, {llm.MODEL} (common/common_helpers/llm.py), isn't in the list, so a step run without "
                  f"--model may be refused at its test call. Give one of the models above with --model <name>.")
        return
    tried = try_models(args.wanted, names, args.service)
    usable = [n for n, ok, _ in tried if ok]
    print(f"\n{len(usable)} of {len(tried)} usable" + (f": {', '.join(usable)}" if usable else "") + ". To use one, "
          f"give it to a step's settings, e.g. `py 060_extract/run.py --service {args.service} --model <name>`.")


if __name__ == "__main__":
    main()
