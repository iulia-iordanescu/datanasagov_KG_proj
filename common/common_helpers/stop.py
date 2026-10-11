"""
common/common_helpers/stop.py -- Stop: a problem the person can fix, found by a check.

    from common.stop import Stop
    raise Stop("annotations/ground_truth_candidates.csv lists these ids more than once: …; fix the file")

The message says what is wrong and what to do. A step that meets one stops:
run_step (common/common_helpers/step.py) reports the run as "stopped", like a
run the person stopped on purpose, not "failed", which is kept for bugs in
the code (any other exception). The annotation tool, which shares some of the
readers that raise it, shows the message like any other problem: Stop is a
ValueError, so it is caught where a ValueError is.
"""


class Stop(ValueError):
    """A check's finding the person can fix; the message says what to do."""
