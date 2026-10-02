#!/usr/bin/env python3
"""Validate the Cohestra repository.

The checks cover what fails silently in a client: manifests, agent visibility,
delegation limits, Claude mirrors, the portable skill, eval cases, workflows,
forbidden components, stale names, and file hygiene.

Usage:
    python3 scripts/validate.py                  # offline checks
    python3 scripts/validate.py --require-yaml   # fail when PyYAML is missing (CI)
    python3 scripts/validate.py --online         # also compare with the live schema

The default run makes no network calls. The --online flag fetches the Agent
Plugins schema. When the fetch fails, the script warns and keeps the local result.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cohestra_common as c  # noqa: E402

try:  # PyYAML is optional. CI installs it.
    import yaml
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None

REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".editorconfig",
    ".gitattributes",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/plugin/marketplace.json",
    ".github/pull_request_template.md",
    ".github/workflows/eval.yml",
    ".github/workflows/release.yml",
    ".github/workflows/validate.yml",
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "REPOSITORY.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docs/ARCHITECTURE.md",
    "docs/DEVELOPMENT.md",
    "docs/PRODUCT.md",
    "docs/TESTING.md",
    "plugin.json",
    "scripts/cohestra_common.py",
    "scripts/package.py",
    "scripts/release_notes.py",
    "scripts/sync_claude_agents.py",
    "scripts/validate.py",
    "skills/cohestra-engineering/SKILL.md",
    "tests/run.py",
    "tests/test_repository.py",
]

# Files that hold stale names, secret patterns, or banned words as test data.
SELF_REFERENCE = {"scripts/validate.py", "tests/test_repository.py", "tests/run.py"}

# (pattern, label, flags). The placeholder pattern is case-sensitive, so ordinary
# prose such as "the repository owner" is not a false match.
STALE_PATTERNS = [
    (r"multi-agent-review-coordinator", "old plugin name", re.IGNORECASE),
    (r"agent-review-suite", "old plugin name", re.IGNORECASE),
    (r"review[ -]orchestrator", "old agent name", re.IGNORECASE),
    (r"coordinated[ -]software[ -]review", "old tagline", re.IGNORECASE),
    (r"multi-agent review coordinator", "old product name", re.IGNORECASE),
    (r"agent review suite", "old product name", re.IGNORECASE),
    (r"lean-repository-review|coordinated-repository-review", "old skill name", re.IGNORECASE),
    (r"(?<![\d.])[45]\.0\.0(?![\d.])", "old version", 0),
    (r"OWNER/REPO(?:SITORY)?\b", "placeholder repository", 0),
    (r"Repository owner", "placeholder owner", 0),
    (r"<owner>|YOUR[_-](?:NAME|ORG|REPO)", "placeholder value", re.IGNORECASE),
]

SECRET_PATTERNS = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private key"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", "GitHub token"),
    (r"\bsk-ant-[A-Za-z0-9_-]{10,}", "Anthropic API key"),
    (r"(?:/home/[a-z][\w.-]*/|/Users/[A-Za-z][\w.-]*/|[A-Za-z]:\\Users\\)", "personal machine path"),
]

FORBIDDEN_NAMES = {
    "hooks": "hooks directory",
    "hooks.json": "hook configuration",
    "mcp.json": "MCP configuration",
    ".mcp.json": "MCP configuration",
    "install.sh": "install script",
    "install.ps1": "install script",
    "install.bat": "install script",
    "postinstall.sh": "install script",
    "preinstall.sh": "install script",
}
FORBIDDEN_KEYS = {"hooks", "mcpServers", "mcp-servers"}

CONTRACT_LINES = [
    "Work only on the delegated task.",
    "Read the minimum required context.",
    "Search before you open large files.",
    "Use targeted ranges or symbols when the client supports them.",
    "Follow repository instructions and local patterns.",
    "Do not expand the scope without a clear reason.",
    "Do not invoke another agent.",
    "Do not commit, push, merge, publish, or deploy.",
    "Return concise evidence and file paths.",
    "State uncertainty and blocked checks.",
    "Do not claim that a test or command passed unless it ran and returned a successful result.",
]
HANDBACK_FIELDS = ["Result:", "Evidence:", "Files changed:", "Checks:", "Risks:", "Needs from coordinator:"]
FINAL_RESPONSE = ["Result", "Work completed", "Files changed", "Checks run", "Risks", "Open questions"]

REQUIRED_CASES = [
    "delegates-context-map",
    "plans-architecture-without-edits",
    "implements-focused-change",
    "delegates-security-review",
    "improves-tests",
    "updates-documentation",
    "writes-from-pattern",
    "completes-engineering-task",
    "reviews-without-edits",
    "unrelated-request",
]
PROMPT_KEYS = {
    "schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome",
    "model", "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env",
}
CASE_TOOLS = {"Read", "Glob", "Grep", "Agent", "Skill", "Write", "Edit"}
GRADER_KEYS = {
    "regex": {"pattern", "flags", "match", "target"},
    "tool_used": {"tool", "input_match", "min", "max"},
    "tool_order": {"before", "after"},
    "file_exists": {"path", "exists"},
    "llm": {"criteria", "focus"},
    "baseline": {"baseline_file", "criteria"},
}
GRADER_COMMON = {"type", "weight", "arm"}

BANNED_WORDS = [
    "simply", "obviously", "just", "worker", "workers", "revolutionary", "seamless",
    "seamlessly", "cutting-edge", "game-changing", "best-in-class", "supercharge",
    "effortless", "effortlessly",
]
CONTRACTION = re.compile(
    r"\b(?:\w+n't|(?:it|that|there|here|what|you|we|they|he|she|let)'(?:s|re|ll|ve|d))\b",
    re.IGNORECASE,
)
MAX_SENTENCE_WORDS = 28


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(report: Report, root: Path, relative: str):
    path = root / relative
    if not path.is_file():
        return None
    try:
        return json.loads(c.read_text(path), object_pairs_hook=_no_duplicates)
    except (ValueError, UnicodeDecodeError) as error:
        report.fail(f"{relative}: invalid JSON: {error}")
        return None


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key '{key}'")
        result[key] = value
    return result


def read_frontmatter(report: Report, root: Path, path: Path):
    """Return (meta, body) or None. Check the YAML subset and PyYAML agreement."""
    name = rel(root, path)
    try:
        text = c.read_text(path)
        raw, body = c.split_frontmatter(text)
        meta = c.parse_frontmatter(raw)
    except (c.FrontmatterError, UnicodeDecodeError) as error:
        report.fail(f"{name}: invalid YAML frontmatter: {error}")
        return None
    if yaml is not None:
        try:
            loaded = yaml.safe_load(raw) if raw.strip() else {}
        except yaml.YAMLError as error:
            report.fail(f"{name}: invalid YAML frontmatter: {error}")
            return None
        if (loaded or {}) != meta:
            report.fail(f"{name}: frontmatter differs between the built-in parser and PyYAML")
            return None
    return meta, body


# --- Repository-wide checks --------------------------------------------------


def check_required_files(report: Report, root: Path) -> None:
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            report.fail(f"missing required file: {relative}")


def check_text_files(report: Report, root: Path) -> int:
    """Check encoding, line endings, final newline, stale names, and secrets."""
    count = 0
    for path in c.iter_repo_files(root):
        name = rel(root, path)
        data = path.read_bytes()
        count += 1
        if b"\x00" in data:
            report.fail(f"{name}: binary file. The package must contain text files only")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            report.fail(f"{name}: not valid UTF-8")
            continue
        if "\r" in text:
            report.fail(f"{name}: contains a carriage return. Use LF line endings")
        if text and not text.endswith("\n"):
            report.fail(f"{name}: missing final newline")
        elif text.endswith("\n\n"):
            report.fail(f"{name}: more than one newline at the end of the file")
        if name in SELF_REFERENCE:
            continue
        for pattern, label, flags in STALE_PATTERNS:
            if re.search(pattern, text, flags):
                report.fail(f"{name}: stale or placeholder value ({label}): /{pattern}/")
        for repo in re.findall(r"github\.com/mbaic/([A-Za-z0-9._-]+)", text):
            if repo != c.REPOSITORY_NAME:
                report.fail(f"{name}: repository URL names '{repo}'. It must name '{c.REPOSITORY_NAME}'")
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, text):
                report.fail(f"{name}: possible {label}")
    return count


def check_json_files(report: Report, root: Path) -> None:
    for path in c.iter_repo_files(root):
        if path.suffix == ".json":
            read_json(report, root, rel(root, path))


def check_yaml_files(report: Report, root: Path, require_yaml: bool) -> None:
    files = [p for p in c.iter_repo_files(root) if p.suffix in {".yml", ".yaml"}]
    for path in files:
        name = rel(root, path)
        text = c.read_text(path)
        if re.search(r"^\t", text, re.MULTILINE):
            report.fail(f"{name}: tab character in YAML indentation")
    if yaml is None:
        message = "PyYAML is not installed. YAML files got a tab check only"
        (report.fail if require_yaml else report.warn)(message)
        return
    for path in files:
        name = rel(root, path)
        try:
            docs = list(yaml.safe_load_all(c.read_text(path)))
        except yaml.YAMLError as error:
            report.fail(f"{name}: invalid YAML: {error}")
            continue
        if not docs or docs[0] is None:
            report.fail(f"{name}: empty YAML file")
        elif path.parent.name == "ISSUE_TEMPLATE" and path.name != "config.yml":
            form = docs[0]
            for key in ("name", "description", "body"):
                if not isinstance(form, dict) or key not in form:
                    report.fail(f"{name}: issue form is missing '{key}'")
            if isinstance(form, dict) and isinstance(form.get("body"), list):
                for item in form["body"]:
                    if not isinstance(item, dict) or "type" not in item:
                        report.fail(f"{name}: every issue form body item needs a 'type'")


def check_forbidden(report: Report, root: Path) -> None:
    for path in c.iter_repo_files(root):
        relative = path.relative_to(root)
        for part in relative.parts:
            if part in FORBIDDEN_NAMES:
                report.fail(f"forbidden component ({FORBIDDEN_NAMES[part]}): {relative.as_posix()}")
        if relative.as_posix() == ".github/mcp.json":
            report.fail("forbidden component (MCP configuration): .github/mcp.json")
    for directory in root.rglob("hooks"):
        if directory.is_dir() and not any(p in c.SKIP_DIRS for p in directory.relative_to(root).parts):
            report.fail(f"forbidden component (hooks directory): {rel(root, directory)}")
    if (root / "setup.py").exists() or (root / "package.json").exists():
        report.fail("install-time script entry point found (setup.py or package.json)")
    # Network client code is not allowed in the plugin package. Developer scripts
    # under scripts/ and tests/ may read and write local files and may fetch the schema.
    pattern = re.compile(r"\b(?:curl|wget|urllib|requests\.|http\.client|socket\.|fetch\()")
    for path in c.iter_repo_files(root):
        relative = path.relative_to(root)
        if relative.parts[0] in {"scripts", "tests", "docs", ".github"}:
            continue
        if path.suffix in {".py", ".sh", ".js", ".ts", ".ps1"} and pattern.search(c.read_text(path)):
            if relative.parts[0] == "evals":
                continue  # Fixture code is test data. It never runs in the plugin.
            report.fail(f"network client code in the package: {relative.as_posix()}")


def check_gitignore(report: Report, root: Path) -> None:
    path = root / ".gitignore"
    if not path.is_file():
        return
    lines = {line.strip() for line in c.read_text(path).splitlines()}
    for entry in ("evals/results/", "dist/", "__pycache__/"):
        if entry not in lines:
            report.fail(f".gitignore must contain '{entry}'")
    results = root / "evals" / "results"
    if results.exists() and (root / ".git").exists() and shutil.which("git"):
        tracked = subprocess.run(
            ["git", "ls-files", "evals/results"], cwd=root, capture_output=True, text=True
        ).stdout.split()
        if tracked:
            report.fail("evals/results/ content is tracked by Git: " + ", ".join(tracked[:3]))


# --- Manifests ----------------------------------------------------------------


def check_manifests(report: Report, root: Path, online: bool) -> None:
    manifest = read_json(report, root, "plugin.json")
    if manifest is not None:
        for error in c.schema_errors(manifest, c.PLUGIN_SCHEMA):
            report.fail(f"plugin.json: schema: {error}")
        expect = {
            "name": c.PLUGIN_NAME,
            "version": c.PLUGIN_VERSION,
            "description": c.PLUGIN_DESCRIPTION,
            "homepage": c.REPOSITORY_URL,
            "repository": c.REPOSITORY_URL,
            "license": c.LICENSE_ID,
        }
        for key, value in expect.items():
            if manifest.get(key) != value:
                report.fail(f"plugin.json: '{key}' must be {value!r}, found {manifest.get(key)!r}")
        author = manifest.get("author") or {}
        if author.get("name") != c.AUTHOR_NAME or author.get("url") != c.AUTHOR_URL:
            report.fail("plugin.json: author must be Milos Baic with the GitHub owner URL")
        if online:
            check_online_schema(report, manifest)

    claude = read_json(report, root, ".claude-plugin/plugin.json")
    if claude is not None:
        allowed = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"}
        for key in sorted(set(claude) - allowed):
            report.fail(f".claude-plugin/plugin.json: unsupported field '{key}'")
        for key in ("name", "version", "description", "homepage", "repository", "license"):
            if manifest is not None and claude.get(key) != manifest.get(key):
                report.fail(f".claude-plugin/plugin.json: '{key}' differs from plugin.json")
        if claude.get("name") != c.PLUGIN_NAME:
            report.fail(f".claude-plugin/plugin.json: name must be {c.PLUGIN_NAME!r}")
        if claude.get("version") != c.PLUGIN_VERSION:
            report.fail(f".claude-plugin/plugin.json: version must be {c.PLUGIN_VERSION!r}")

    market = read_json(report, root, ".github/plugin/marketplace.json")
    if market is not None:
        if market.get("name") != c.REPOSITORY_NAME:
            report.fail(f"marketplace.json: name must be {c.REPOSITORY_NAME!r}")
        if (market.get("owner") or {}).get("name") != c.AUTHOR_NAME:
            report.fail("marketplace.json: owner.name must be Milos Baic")
        if (market.get("metadata") or {}).get("version") != c.PLUGIN_VERSION:
            report.fail(f"marketplace.json: metadata.version must be {c.PLUGIN_VERSION!r}")
        plugins = market.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            report.fail("marketplace.json: it must list exactly one plugin")
        else:
            entry = plugins[0]
            if entry.get("name") != c.PLUGIN_NAME:
                report.fail(f"marketplace.json: plugin name must be {c.PLUGIN_NAME!r}")
            if entry.get("source") != "./":
                report.fail("marketplace.json: plugin source must be './'")
            if entry.get("version") != c.PLUGIN_VERSION:
                report.fail(f"marketplace.json: plugin version must be {c.PLUGIN_VERSION!r}")
            if manifest is not None and entry.get("name") != manifest.get("name"):
                report.fail("marketplace.json: plugin name differs from plugin.json")

    for relative in ("plugin.json", ".claude-plugin/plugin.json", ".github/plugin/marketplace.json"):
        data = read_json(report, root, relative)
        if isinstance(data, dict):
            for key in FORBIDDEN_KEYS & set(data):
                report.fail(f"{relative}: forbidden key '{key}'")


def _strip_docs(value):
    if isinstance(value, dict):
        return {k: _strip_docs(v) for k, v in value.items() if k not in {"description", "title", "$comment"}}
    return value


def check_online_schema(report: Report, manifest: dict) -> None:
    import urllib.request

    try:
        with urllib.request.urlopen(c.PLUGIN_SCHEMA_ID, timeout=10) as response:  # noqa: S310
            live = json.load(response)
    except Exception as error:  # Any failure is a warning. The local check still ran.
        report.warn(
            f"live schema check unavailable ({type(error).__name__}). "
            "The local structural check ran"
        )
        return
    if _strip_docs(live) != _strip_docs(c.PLUGIN_SCHEMA):
        report.warn("the live schema differs from the embedded copy. Update PLUGIN_SCHEMA")
    for error in c.schema_errors(manifest, live):
        report.fail(f"plugin.json: live schema: {error}")


# --- Agents -------------------------------------------------------------------


def check_agents(report: Report, root: Path) -> None:
    source = root / c.COPILOT_DIR
    expected_files = {f"{agent_id}{c.COPILOT_SUFFIX}" for agent_id in c.ALL_AGENT_IDS}
    present = {p.name for p in source.glob("*") if p.is_file()} if source.is_dir() else set()
    for name in sorted(expected_files - present):
        report.fail(f"missing agent file: {(c.COPILOT_DIR / name).as_posix()}")
    for name in sorted(present - expected_files):
        report.fail(f"unexpected file in {c.COPILOT_DIR.as_posix()}: {name}")

    visible: list[str] = []
    for agent_id in c.ALL_AGENT_IDS:
        path = source / f"{agent_id}{c.COPILOT_SUFFIX}"
        if not path.is_file():
            continue
        loaded = read_frontmatter(report, root, path)
        if loaded is None:
            continue
        meta, body = loaded
        name = rel(root, path)
        for key in sorted(set(meta) - c.COPILOT_KEYS):
            if key == "target":
                report.fail(f"{name}: 'target' is not allowed. Omit it so the agent runs in every client")
            elif key == "model":
                report.fail(f"{name}: 'model' is not allowed. Let the user choose the model")
            else:
                report.fail(f"{name}: unsupported frontmatter key '{key}'")
        if meta.get("name") != c.DISPLAY_NAMES[agent_id]:
            report.fail(f"{name}: name must be {c.DISPLAY_NAMES[agent_id]!r}, found {meta.get('name')!r}")
        description = meta.get("description")
        if not isinstance(description, str) or not description.strip():
            report.fail(f"{name}: description is required")
        tools = meta.get("tools")
        if not isinstance(tools, list) or not tools:
            report.fail(f"{name}: tools must be a non-empty list")
        else:
            unknown = set(tools) - set(c.TOOL_MAP)
            extra = set(tools) - c.TOOL_POLICY[agent_id]
            if unknown:
                report.fail(f"{name}: unknown tool alias: {', '.join(sorted(unknown))}")
            if extra - unknown:
                report.fail(f"{name}: tools exceed the policy: {', '.join(sorted(extra - unknown))}")
            if agent_id == c.COORDINATOR_ID and set(tools) != c.TOOL_POLICY[agent_id]:
                report.fail(f"{name}: the coordinator tools must be exactly read, search, agent")
        if meta.get("user-invocable", True) is not False:
            visible.append(str(meta.get("name")))

        if agent_id == c.COORDINATOR_ID:
            check_coordinator(report, name, meta, body)
        else:
            check_specialist(report, name, meta, body)

    if len(visible) != 1:
        report.fail(f"exactly one Copilot agent must be visible, found {len(visible)}: {visible}")
    elif visible[0] != c.COORDINATOR_NAME:
        report.fail(f"the visible agent must be {c.COORDINATOR_NAME!r}, found {visible[0]!r}")

    check_mirrors(report, root)


def check_coordinator(report: Report, name: str, meta: dict, body: str) -> None:
    if meta.get("user-invocable") is not True:
        report.fail(f"{name}: the coordinator must set user-invocable: true")
    if meta.get("disable-model-invocation") is not True:
        report.fail(f"{name}: the coordinator must set disable-model-invocation: true")
    allow = meta.get("agents")
    if not isinstance(allow, list):
        report.fail(f"{name}: the coordinator needs an explicit agents allowlist")
    else:
        outside = [item for item in allow if item not in c.SPECIALIST_NAMES]
        missing = [item for item in c.SPECIALIST_NAMES if item not in allow]
        if outside:
            report.fail(f"{name}: delegation outside the Cohestra roster: {outside}")
        if missing:
            report.fail(f"{name}: allowlist is missing specialists: {missing}")
        if len(allow) != len(set(allow)):
            report.fail(f"{name}: allowlist has duplicate entries")
    for agent_id, display in c.SPECIALISTS:
        if display not in body or f"`{agent_id}`" not in body:
            report.fail(f"{name}: the prompt must name {display} and `{agent_id}`")
    for number in range(1, 16):
        if not re.search(rf"^{number}\. ", body, re.MULTILINE):
            report.fail(f"{name}: coordinator method step {number} is missing")
    for line in FINAL_RESPONSE:
        if not re.search(rf"^{re.escape(line)}$", body, re.MULTILINE):
            report.fail(f"{name}: final response structure is missing '{line}'")


def check_specialist(report: Report, name: str, meta: dict, body: str) -> None:
    if meta.get("user-invocable") is not False:
        report.fail(f"{name}: a specialist must set user-invocable: false")
    if meta.get("disable-model-invocation") is not False:
        report.fail(f"{name}: a specialist must set disable-model-invocation: false")
    if meta.get("agents") != []:
        report.fail(f"{name}: a specialist must set agents: []. It cannot delegate")
    if "agent" in (meta.get("tools") or []):
        report.fail(f"{name}: a specialist must not have the agent tool")
    for line in CONTRACT_LINES:
        if f"- {line}" not in body:
            report.fail(f"{name}: specialist contract line is missing: {line!r}")
    for field in HANDBACK_FIELDS:
        if not re.search(rf"^{re.escape(field)}$", body, re.MULTILINE):
            report.fail(f"{name}: handback field is missing: {field}")


def check_mirrors(report: Report, root: Path) -> None:
    target = root / c.CLAUDE_DIR
    expected_names = {f"{agent_id}.md" for agent_id in c.ALL_AGENT_IDS}
    present = {p.name for p in target.glob("*") if p.is_file()} if target.is_dir() else set()
    for name in sorted(expected_names - present):
        report.fail(f"missing Claude mirror: {(c.CLAUDE_DIR / name).as_posix()}")
    for name in sorted(present - expected_names):
        report.fail(f"unexpected file in {c.CLAUDE_DIR.as_posix()}: {name}")
    try:
        expected = c.expected_mirrors(root)
    except (c.FrontmatterError, ValueError, OSError) as error:
        report.fail(f"cannot build Claude mirrors: {error}")
        return
    for path, text in expected.items():
        if path.is_file() and c.read_text(path) != text:
            report.fail(
                f"{rel(root, path)}: differs from its Copilot source. "
                "Run: python3 scripts/sync_claude_agents.py"
            )
    for path in sorted(target.glob("*.md")) if target.is_dir() else []:
        loaded = read_frontmatter(report, root, path)
        if loaded is None:
            continue
        meta, _ = loaded
        for key in sorted(set(meta) - {"name", "description", "tools"}):
            report.fail(f"{rel(root, path)}: Copilot-only or unsupported field '{key}'")
        if meta.get("name") != path.stem:
            report.fail(f"{rel(root, path)}: name must be {path.stem!r}")


# --- Skill --------------------------------------------------------------------


def check_skill(report: Report, root: Path) -> None:
    skills = root / "skills"
    folders = sorted(p.name for p in skills.iterdir() if p.is_dir()) if skills.is_dir() else []
    if folders != [c.SKILL_NAME]:
        report.fail(f"skills/ must hold only '{c.SKILL_NAME}', found {folders}")
    path = skills / c.SKILL_NAME / "SKILL.md"
    if not path.is_file():
        return
    loaded = read_frontmatter(report, root, path)
    if loaded is None:
        return
    meta, body = loaded
    name = meta.get("name")
    if name != c.SKILL_NAME:
        report.fail(f"{rel(root, path)}: name must equal the directory name {c.SKILL_NAME!r}, found {name!r}")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        report.fail(f"{rel(root, path)}: invalid skill name {name!r}")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        report.fail(f"{rel(root, path)}: description must have 1 to 1024 characters")
    for key in sorted(set(meta) - {"name", "description", "license"}):
        report.fail(f"{rel(root, path)}: unsupported skill frontmatter key '{key}'")
    if not body.strip():
        report.fail(f"{rel(root, path)}: the skill body is empty")


# --- Evals --------------------------------------------------------------------


def case_dirs(root: Path) -> list[Path]:
    base = root / "evals"
    if not base.is_dir():
        return []
    found = []
    for path in sorted(base.rglob("*")):
        if path.is_dir() and (path / "prompt.md").is_file() or path.name == "case.yaml":
            found.append(path if path.is_dir() else path.parent)
    return sorted(set(p for p in found if "results" not in p.relative_to(base).parts))


def check_evals(report: Report, root: Path) -> None:
    cases = case_dirs(root)
    names = {p.name for p in cases}
    for required in REQUIRED_CASES:
        if required not in names:
            report.fail(f"missing required eval case: evals/{required}")
    for case in cases:
        name = rel(root, case)
        prompt = case / "prompt.md"
        meta: dict = {}
        if prompt.is_file():
            loaded = read_frontmatter(report, root, prompt)
            if loaded is not None:
                meta, body = loaded
                if not body.strip():
                    report.fail(f"{name}/prompt.md: the prompt is empty")
        for key in sorted(set(meta) - PROMPT_KEYS):
            report.fail(f"{name}/prompt.md: unknown frontmatter key '{key}'")
        for key in ("runs", "max_turns", "timeout_seconds", "allowed_tools", "tags"):
            if key not in meta:
                report.fail(f"{name}/prompt.md: run limit or tool list is missing: {key}")
        if meta.get("plugins") != ["../.."]:
            report.fail(f"{name}/prompt.md: plugins must be [\"../..\"]")
        tools = meta.get("allowed_tools") or []
        if isinstance(tools, list) and set(tools) - CASE_TOOLS:
            report.fail(f"{name}/prompt.md: tools outside the approved set: {sorted(set(tools) - CASE_TOOLS)}")
        check_case_yaml(report, root, case)
        check_graders(report, root, case)


def check_case_yaml(report: Report, root: Path, case: Path) -> None:
    path = case / "case.yaml"
    if not path.is_file():
        return
    text = c.read_text(path)
    script = None
    if yaml is not None:
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError as error:
            report.fail(f"{rel(root, path)}: invalid YAML: {error}")
            return
        if data.get("schema_version") != "1.1":
            report.fail(f"{rel(root, path)}: schema_version must be \"1.1\"")
        if data.get("name") != case.name:
            report.fail(f"{rel(root, path)}: name must equal the directory name {case.name!r}")
        script = (data.get("context") or {}).get("scaffold_script")
    else:
        match = re.search(r"^\s*scaffold_script:\s*(\S+)", text, re.MULTILINE)
        script = match.group(1) if match else None
    if script:
        fixture = case / script
        if not fixture.is_file():
            report.fail(f"{rel(root, path)}: scaffold script not found: {script}")
        else:
            first = c.read_text(fixture).splitlines()[0] if c.read_text(fixture) else ""
            if not first.startswith("#!"):
                report.fail(f"{rel(root, fixture)}: missing shebang line")
            bash = shutil.which("bash")
            if bash:
                result = subprocess.run([bash, "-n", str(fixture)], capture_output=True, text=True)
                if result.returncode != 0:
                    report.fail(f"{rel(root, fixture)}: shell syntax error: {result.stderr.strip()}")


def check_graders(report: Report, root: Path, case: Path) -> None:
    name = rel(root, case)
    files = sorted((case / "graders").glob("*.md")) if (case / "graders").is_dir() else []
    inline = 0
    case_yaml = case / "case.yaml"
    if case_yaml.is_file() and yaml is not None:
        try:
            inline = len((yaml.safe_load(c.read_text(case_yaml)) or {}).get("graders") or [])
        except yaml.YAMLError:
            inline = 0
    if not files and not inline:
        report.fail(f"{name}: the case has no grader")
        return
    types: list[str] = []
    for path in files:
        loaded = read_frontmatter(report, root, path)
        if loaded is None:
            continue
        meta, body = loaded
        kind = meta.get("type")
        gname = rel(root, path)
        if kind not in GRADER_KEYS:
            report.fail(f"{gname}: unknown grader type {kind!r}")
            continue
        types.append(kind)
        for key in sorted(set(meta) - GRADER_KEYS[kind] - GRADER_COMMON):
            report.fail(f"{gname}: unknown key '{key}' for a {kind} grader")
        required = {"regex": "pattern", "tool_used": "tool", "file_exists": "path"}.get(kind)
        if required and required not in meta:
            report.fail(f"{gname}: a {kind} grader needs '{required}'")
        if kind == "tool_order" and not {"before", "after"} <= set(meta):
            report.fail(f"{gname}: a tool_order grader needs 'before' and 'after'")
        if kind == "llm" and not (body.strip() or meta.get("criteria")):
            report.fail(f"{gname}: an llm grader needs criteria in the body")
        for key in ("pattern", "input_match"):
            if isinstance(meta.get(key), str):
                try:
                    re.compile(meta[key])
                except re.error as error:
                    report.fail(f"{gname}: invalid regular expression in '{key}': {error}")
        match = meta.get("input_match")
        if isinstance(match, str) and "cohestra" in match:
            if not match.startswith("cohestra:"):
                report.fail(f"{gname}: input_match must start with the namespace 'cohestra:'")
            for token in re.findall(r"cohestra-[a-z]+(?:-[a-z]+)*", match):
                if token not in c.ALL_AGENT_IDS:
                    report.fail(f"{gname}: input_match names an unknown agent: {token}")
    if types and all(kind in {"llm", "baseline"} for kind in types) and not inline:
        report.fail(f"{name}: the case relies only on LLM graders. Add a deterministic grader")


# --- Workflows ------------------------------------------------------------------


def triggers(document: dict) -> set[str]:
    on = document.get("on", document.get(True))
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return set(on)
    if isinstance(on, dict):
        return set(on)
    return set()


WORKFLOWS = {"validate.yml", "eval.yml", "release.yml"}


def check_workflows(report: Report, root: Path) -> None:
    base = root / ".github" / "workflows"
    # A leftover workflow can run paid evals or publish without the guards below.
    if base.is_dir():
        for path in sorted(base.iterdir()):
            if path.name not in WORKFLOWS:
                report.fail(f"unexpected workflow: .github/workflows/{path.name}")
    texts = {n: c.read_text(base / n) for n in ("validate.yml", "eval.yml", "release.yml") if (base / n).is_file()}
    docs = {}
    if yaml is not None:
        for name, text in texts.items():
            try:
                docs[name] = yaml.safe_load(text) or {}
            except yaml.YAMLError:
                docs[name] = {}
    for name, text in texts.items():
        if not re.search(r"^permissions:", text, re.MULTILINE):
            report.fail(f"workflows/{name}: declare top-level permissions")
        prints_secret = re.search(r"(?:echo|printf|cat)[^\n]*(?:\$\{?ANTHROPIC_API_KEY|\$\{\{\s*secrets\.)", text)
        if prints_secret or re.search(r"^\s*set -x", text, re.MULTILINE):
            report.fail(f"workflows/{name}: a step can print a secret")
    if docs:
        if not {"push", "pull_request"} <= triggers(docs.get("validate.yml", {})):
            report.fail("workflows/validate.yml: it must run on push and pull_request")
        for name in ("eval.yml", "release.yml"):
            if name in docs and triggers(docs[name]) != {"workflow_dispatch"}:
                report.fail(f"workflows/{name}: it must run only on workflow_dispatch")
    ev = texts.get("eval.yml", "")
    for flag in ("--trust-plugin", "--scaffold", "--json", "--no-publish", "--threshold",
                 "--max-cost-usd", "--model", "--judge-model", "ANTHROPIC_API_KEY", "upload-artifact"):
        if ev and flag not in ev:
            report.fail(f"workflows/eval.yml: missing {flag}")
    rel_text = texts.get("release.yml", "")
    for needle in (c.PLUGIN_VERSION, "scripts/package.py", "sha256", "gh release create", "workflow_dispatch"):
        if rel_text and needle not in rel_text:
            report.fail(f"workflows/release.yml: missing {needle!r}")
    val = texts.get("validate.yml", "")
    for needle in ("sync_claude_agents.py --check", "scripts/validate.py", "tests/run.py"):
        if val and needle not in val:
            report.fail(f"workflows/validate.yml: missing {needle!r}")


# --- Writing standard -------------------------------------------------------------


def prose(text: str) -> str:
    """Return markdown text without fenced code, inline code, tables, and frontmatter."""
    try:
        _, text = c.split_frontmatter(text)
    except c.FrontmatterError:
        pass
    text = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.MULTILINE | re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    return re.sub(r"https?://\S+", "", text)


def check_writing(report: Report, root: Path) -> None:
    long_sentences = 0
    for path in c.iter_repo_files(root):
        relative = path.relative_to(root)
        if path.suffix != ".md" or relative.parts[0] in {"evals", "tests"}:
            continue
        name = relative.as_posix()
        text = prose(c.read_text(path))
        for word in BANNED_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                report.fail(f"{name}: avoid the word '{word}'")
        for match in CONTRACTION.finditer(text):
            report.fail(f"{name}: avoid the contraction '{match.group(0)}'")
        if re.search(r"\bautonomous team\b", text, re.IGNORECASE):
            report.fail(f"{name}: avoid the claim 'autonomous team'")
        if name in {"README.md"} or relative.parts[0] == "docs":
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", re.sub(r"^[#>*\-\d. ]+", "", text, flags=re.MULTILINE)):
                if len(sentence.split()) > MAX_SENTENCE_WORDS:
                    long_sentences += 1
                    if long_sentences <= 10:
                        report.warn(f"{name}: sentence over {MAX_SENTENCE_WORDS} words: {sentence.strip()[:70]}...")
    if long_sentences > 10:
        report.warn(f"{long_sentences - 10} more long sentences not listed")


def check_license(report: Report, root: Path) -> None:
    path = root / "LICENSE"
    if path.is_file():
        text = c.read_text(path)
        if "MIT License" not in text or f"Copyright (c) 2026 {c.AUTHOR_NAME}" not in text:
            report.fail("LICENSE: must be the MIT License with the copyright holder Milos Baic")


# --- Entry point ------------------------------------------------------------------


def run(root: Path, online: bool = False, require_yaml: bool = False) -> tuple[Report, int]:
    report = Report()
    check_required_files(report, root)
    checked = check_text_files(report, root)
    check_json_files(report, root)
    check_yaml_files(report, root, require_yaml)
    check_forbidden(report, root)
    check_gitignore(report, root)
    check_manifests(report, root, online)
    check_agents(report, root)
    check_skill(report, root)
    check_evals(report, root)
    check_workflows(report, root)
    check_writing(report, root)
    check_license(report, root)
    return report, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--online", action="store_true", help="also compare with the live Agent Plugins schema")
    parser.add_argument("--require-yaml", action="store_true", help="fail when PyYAML is not installed")
    parser.add_argument("--root", type=Path, default=c.ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    report, checked = run(args.root.resolve(), args.online, args.require_yaml)
    for warning in report.warnings:
        print(f"warning: {warning}")
    if report.errors:
        print("Validation failed:")
        for error in report.errors:
            print(f"- {error}")
        return 1
    print(
        f"Validation passed: {c.COORDINATOR_NAME} is the only visible agent; "
        f"{len(c.SPECIALISTS)} specialists are hidden and callable; "
        f"{checked} files checked; no hooks or MCP server."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
