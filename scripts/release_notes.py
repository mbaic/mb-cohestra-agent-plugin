#!/usr/bin/env python3
"""Print one version section of CHANGELOG.md for use as release notes.

Usage:
    python3 scripts/release_notes.py 0.1.0

The script exits 1 when the version has no section or when the section is
empty. A release without a changelog entry is a mistake. Empty notes would hide it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def extract(version: str, text: str) -> str | None:
    """Return the body of the section for version, or None when it is absent.

    The heading can be '## [0.1.0] - 2026-10-02' or '## 0.1.0 - 2026-10-02'.
    """
    heading = re.compile(rf"^##\s+\[?{re.escape(version)}\]?(?:\s|$)", re.MULTILINE)
    match = heading.search(text)
    if not match:
        return None
    line_end = text.find("\n", match.end())
    start = len(text) if line_end == -1 else line_end + 1
    following = re.compile(r"^##\s+", re.MULTILINE).search(text, start)
    body = text[start : following.start()] if following else text[start:]
    # Link definitions such as "[0.1.0]: https://..." belong to the changelog, not the notes.
    lines = [line for line in body.split("\n") if not re.match(r"^\[[^\]]+\]:\s", line)]
    return "\n".join(lines).strip()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: release_notes.py <version>", file=sys.stderr)
        return 2
    version = argv[1].lstrip("v")
    if not CHANGELOG.is_file():
        print(f"error: {CHANGELOG} not found", file=sys.stderr)
        return 1
    body = extract(version, CHANGELOG.read_text(encoding="utf-8"))
    if body is None:
        print(
            f"error: CHANGELOG.md has no section for version {version}. "
            f"Add a '## [{version}] - <date>' section before you release.",
            file=sys.stderr,
        )
        return 1
    if not body:
        print(f"error: the {version} section of CHANGELOG.md is empty.", file=sys.stderr)
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
