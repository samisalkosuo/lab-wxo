#!/usr/bin/env python3
"""Convenience launcher: `python wxodemo.py <command>` works without installing the package.

After `pip install -e .` the same CLI is also available as the `wxodemo` command.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from wxodemo.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
