#!/usr/bin/env python3
"""Study Loop state engine.

    python3 study_loop.py --workspace /absolute/learning/folder < request.json

Reads one JSON request from stdin and writes one JSON response to stdout.
Exit codes: 0 ok, 2 input/reference/state, 3 conflict/lock, 4 I/O or damaged
records, 5 unsupported protocol/format/runtime.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from studyloop.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
