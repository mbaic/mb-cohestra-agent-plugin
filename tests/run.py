#!/usr/bin/env python3
"""Run the Cohestra unit tests.

Usage:
    python3 tests/run.py        # quiet
    python3 tests/run.py -v     # one line for each test

The tests need no credentials and make no model call. They read repository
files and write only to temporary directories.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent


def main() -> int:
    sys.path.insert(0, str(TESTS))
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py", top_level_dir=str(TESTS))
    verbosity = 2 if "-v" in sys.argv[1:] else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
