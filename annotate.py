"""
annotate.py -- the annotation tool: read and correct triple instances in your
browser.

    py annotate.py              opens http://127.0.0.1:8050 in your browser
    py annotate.py --port 8051  if 8050 is taken

Pick a batch at the top of the page. Opening one of step 050's draft batches
for the first time copies it to annotations/ground_truth/batch_<NNN>.csv, and
every change you make is saved to that copy at once. The "Translation
table" button opens annotations/name_mapping.csv (step 070's table of which
ground truth name each name of the current schema means), row by row, to
check. Press Ctrl+C here to stop the tool.

It runs only on this computer: no internet, no model calls, nothing to
install. It isn't a pipeline step: it writes nothing but your ground truth
files and the translation table. How it works: annotator/server.py; how to use it:
annotations/README.md.
"""
import argparse
import webbrowser

from annotator.server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Read and correct triple instances in your browser.")
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
