"""
helpers/annotate.py -- the annotation tool: correct the ground truth triples a
model drafted, in your browser.

    py helpers/annotate.py               opens http://127.0.0.1:8050 in your browser
    py helpers/annotate.py --port 8051   if 8050 is taken
    py helpers/annotate.py --no-browser  serves the page without opening the browser

The tool opens on its home page, with a box for each view. Ground truth
(pick a batch in its dropdown at the top of the page): opening one of step
050's draft batches for the first time copies it to
annotations/ground_truth/batch_<NNN>.csv, and every change is saved to that
copy at once. Translation table: annotations/component_class_mapping.csv
(step 070's table of which component class of the ground truth schema each
component class of the current schema means), row by row, to check.
Partial pairs: evaluation's partial pairs, to review. Schema additions:
annotations/schema_additions.txt, to edit. An entity class, predicate, or
pattern the ground truth uses but the ground truth schema lacks can be added
to it with a button. Press Ctrl+C here to stop the tool.

It runs only on this computer: no internet, no model calls, nothing to
install. It isn't a pipeline step: it writes nothing but the ground truth
files, the translation table, the partial-pair verdicts, the schema
additions, and the entity classes, predicates, and patterns added to the
ground truth schema. How it works: helpers/annotator/server.py; how to use
it: annotations/README.md.
"""
import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from annotator.server import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="py helpers/annotate.py", description="Correct the ground truth triples a model drafted, in your browser.")
    parser.add_argument("--port", type=int, default=8050, help="the port the page is served on (default 8050)")
    parser.add_argument("--no-browser", action="store_true", help="don't open the browser")
    args = parser.parse_args()

    server = serve(args.port)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"The annotation tool is at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped. Your changes were saved as you made them.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
