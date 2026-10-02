#!/usr/bin/env python3
"""Build the Cohestra release archive and its SHA-256 checksum file.

Usage:
    python3 scripts/package.py [--output-dir dist]

The script runs the sync check and the validator first. It then writes:

    <output-dir>/mb-cohestra-agent-plugin-v<version>.zip
    <output-dir>/mb-cohestra-agent-plugin-v<version>.zip.sha256

The archive has one top-level mb-cohestra-agent-plugin/ directory. Entries have a
fixed order, a fixed timestamp, and fixed permissions, so the same source tree
always gives the same archive. The script reads repository files and writes
local output. It makes no network call.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cohestra_common as c  # noqa: E402

TOP_LEVEL = c.REPOSITORY_NAME
ZIP_DATE = (1980, 1, 1, 0, 0, 0)

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", "dist"}
EXCLUDED_PATHS = ("evals/results",)
EXCLUDED_PATTERNS = [
    "*.zip", "*.pyc", "*.pyo", "*.sha256", "*.log", "*.tmp", "*.swp", "*.bak", "*.orig",
    ".DS_Store", "Thumbs.db",
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    "credentials*", ".npmrc", ".pypirc", ".netrc",
]


def is_excluded(relative: Path) -> bool:
    posix = relative.as_posix()
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if any(posix == path or posix.startswith(path + "/") for path in EXCLUDED_PATHS):
        return True
    return any(fnmatch.fnmatch(relative.name, pattern) for pattern in EXCLUDED_PATTERNS)


def collect(root: Path) -> list[Path]:
    """Return the files to package, sorted by relative path. Hidden files stay in."""
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and not is_excluded(path.relative_to(root))
    ]
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_zip(root: Path, output_dir: Path, version: str) -> tuple[Path, Path, list[str]]:
    """Write the archive and the checksum file. Return (zip, checksum, entry names)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{c.REPOSITORY_NAME}-v{version}.zip"
    entries: list[str] = []
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in collect(root):
            name = f"{TOP_LEVEL}/{path.relative_to(root).as_posix()}"
            data = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, so permissions are the same on every host
            mode = 0o755 if data.startswith(b"#!") else 0o644
            info.external_attr = (0o100000 | mode) << 16
            bundle.writestr(info, data, compresslevel=9)
            entries.append(name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    return archive, checksum, entries


def verify_zip(archive: Path, entries: list[str]) -> list[str]:
    """Return a list of problems found in the finished archive."""
    problems: list[str] = []
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            problems.append("the archive has a corrupt entry")
        names = bundle.namelist()
    if names != entries:
        problems.append("the archive entries differ from the collected files")
    tops = {name.split("/", 1)[0] for name in names}
    if tops != {TOP_LEVEL}:
        problems.append(f"expected one top-level directory '{TOP_LEVEL}', found {sorted(tops)}")
    for name in names:
        relative = Path(name.split("/", 1)[1])
        if is_excluded(relative):
            problems.append(f"excluded file in the archive: {name}")
    for required in ("plugin.json", ".claude-plugin/plugin.json", ".github/plugin/marketplace.json"):
        if f"{TOP_LEVEL}/{required}" not in names:
            problems.append(f"missing from the archive: {required}")
    return problems


def run_checks(root: Path, require_yaml: bool) -> bool:
    scripts = Path(__file__).resolve().parent
    commands = [
        [sys.executable, str(scripts / "sync_claude_agents.py"), "--check", "--root", str(root)],
        [sys.executable, str(scripts / "validate.py"), "--root", str(root)]
        + (["--require-yaml"] if require_yaml else []),
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode != 0:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=Path("dist"), help="where to write the archive")
    parser.add_argument("--require-yaml", action="store_true", help="fail when PyYAML is missing")
    parser.add_argument("--root", type=Path, default=c.ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if not run_checks(root, args.require_yaml):
        print("Packaging stopped: the checks failed.", file=sys.stderr)
        return 1

    version = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
    archive, checksum, entries = build_zip(root, args.output_dir.resolve(), version)
    problems = verify_zip(archive, entries)
    if problems:
        print("Archive check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    digest = checksum.read_text(encoding="utf-8").split()[0]
    print(f"Archive:  {archive}")
    print(f"Checksum: {checksum}")
    print(f"SHA-256:  {digest}")
    print(f"Files:    {len(entries)}")
    print(f"Size:     {archive.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
