#!/usr/bin/env python3
"""Generate or check the Claude Code mirrors of the Cohestra Copilot agents.

Source: com.github.copilot/agents/*.agent.md
Target: agents/*.md

The script keeps each prompt body byte-identical. It writes only the Claude
frontmatter fields: name, description, and tools. It maps Copilot tool aliases
to Claude Code tool names. It needs no network access.

Usage:
    python3 scripts/sync_claude_agents.py            # write the mirrors
    python3 scripts/sync_claude_agents.py --check    # exit 1 when a mirror is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cohestra_common as common  # noqa: E402


def collect(root: Path) -> tuple[dict[Path, str], list[str]]:
    """Return the expected mirrors and a list of source errors."""
    errors: list[str] = []
    source = root / common.COPILOT_DIR
    if not source.is_dir():
        return {}, [f"missing source directory: {common.COPILOT_DIR}"]
    expected: dict[Path, str] = {}
    for path in sorted(source.glob(f"*{common.COPILOT_SUFFIX}")):
        try:
            agent = common.load_agent(path)
            target = root / common.CLAUDE_DIR / f"{agent.agent_id}.md"
            expected[target] = common.render_claude_agent(agent)
        except (common.FrontmatterError, ValueError) as error:
            errors.append(f"{path.relative_to(root)}: {error}")
    return expected, errors


def find_orphans(root: Path, expected: dict[Path, str]) -> list[Path]:
    """Return mirror files that have no Copilot source."""
    target_dir = root / common.CLAUDE_DIR
    if not target_dir.is_dir():
        return []
    return [path for path in sorted(target_dir.glob("*.md")) if path not in expected]


def check(root: Path) -> int:
    expected, errors = collect(root)
    problems = list(errors)
    for target, text in expected.items():
        relative = target.relative_to(root)
        if not target.exists():
            problems.append(f"missing mirror: {relative}")
        elif target.read_text(encoding="utf-8") != text:
            problems.append(f"stale mirror: {relative}")
    for orphan in find_orphans(root, expected):
        problems.append(f"orphan mirror with no Copilot source: {orphan.relative_to(root)}")
    if problems:
        print("Claude mirrors are not in sync:")
        for problem in problems:
            print(f"- {problem}")
        print("Run: python3 scripts/sync_claude_agents.py")
        return 1
    print(f"Claude mirrors are in sync ({len(expected)} files).")
    return 0


def write(root: Path) -> int:
    expected, errors = collect(root)
    if errors:
        print("Cannot sync:")
        for error in errors:
            print(f"- {error}")
        return 1
    (root / common.CLAUDE_DIR).mkdir(exist_ok=True)
    changed = 0
    for target, text in expected.items():
        if target.exists() and target.read_text(encoding="utf-8") == text:
            continue
        target.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {target.relative_to(root)}")
        changed += 1
    for orphan in find_orphans(root, expected):
        orphan.unlink()
        print(f"removed orphan {orphan.relative_to(root)}")
        changed += 1
    print(f"Claude mirrors are in sync ({len(expected)} files, {changed} changed).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write files; exit 1 when a mirror is stale, missing, or orphaned",
    )
    parser.add_argument("--root", type=Path, default=common.ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    return check(args.root) if args.check else write(args.root)


if __name__ == "__main__":
    sys.exit(main())
