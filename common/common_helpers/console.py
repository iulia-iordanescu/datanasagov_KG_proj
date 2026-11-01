"""
common/common_helpers/console.py -- one set-up of the console for every entry point.

A Windows console reads any character, but output redirected to a file or a pipe, or a console in a code page
(cp1252), is encoded in that code page, which has no "✖", "→" or "≠": Python then raises UnicodeEncodeError on the
first such character and the program dies mid-message. setup() makes the standard output and error streams replace
what they can't encode (with "?") instead, so every message arrives. Called first thing by every program a person
runs: run_pipeline.py, the steps (through common.audit.start_log), every helpers/*.py, the annotation tool, and
tests/run_all.py.

    from common.console import setup
    setup()
"""
import sys


def setup() -> None:
    """Make stdout and stderr replace what they can't encode, instead of raising."""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (ValueError, OSError):       # a closed or odd stream: nothing to set up
                pass
