#!/usr/bin/env python3
"""Shared helpers for the Cohestra repository scripts.

Standard library only. These scripts read repository files and write local
output. They do not start background processes or contact a network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Product identity -------------------------------------------------------

PLUGIN_NAME = "cohestra"
PLUGIN_VERSION = "0.1.0"  # Update here, in the manifests, and in CHANGELOG.md.
REPOSITORY_NAME = "mb-cohestra-agent-plugin"
REPOSITORY_URL = "https://github.com/mbaic/mb-cohestra-agent-plugin"
AUTHOR_NAME = "Milos Baic"
AUTHOR_URL = "https://github.com/mbaic"
LICENSE_ID = "MIT"
PLUGIN_DESCRIPTION = (
    "Coordinated software engineering with one coordinator and delegated specialist agents."
)
MARKETPLACE_DESCRIPTION = "Cohestra coordinates specialist AI agents for software engineering."
SKILL_NAME = "cohestra-engineering"
ARCHIVE_NAME = f"{REPOSITORY_NAME}-v{PLUGIN_VERSION}.zip"

# --- Agent roster -----------------------------------------------------------

COORDINATOR_ID = "cohestra-coordinator"
COORDINATOR_NAME = "Cohestra Coordinator"

SPECIALISTS = [
    ("cohestra-context-analyst", "Cohestra Context Analyst"),
    ("cohestra-software-architect", "Cohestra Software Architect"),
    ("cohestra-implementation-engineer", "Cohestra Implementation Engineer"),
    ("cohestra-security-engineer", "Cohestra Security Engineer"),
    ("cohestra-test-engineer", "Cohestra Test Engineer"),
    ("cohestra-quality-engineer", "Cohestra Quality Engineer"),
    ("cohestra-documentation-engineer", "Cohestra Documentation Engineer"),
    ("cohestra-pattern-writer", "Cohestra Pattern Writer"),
]
SPECIALIST_IDS = [agent_id for agent_id, _ in SPECIALISTS]
SPECIALIST_NAMES = [name for _, name in SPECIALISTS]
ALL_AGENT_IDS = [COORDINATOR_ID] + SPECIALIST_IDS
DISPLAY_NAMES = dict(SPECIALISTS) | {COORDINATOR_ID: COORDINATOR_NAME}

# Largest tool set that each Copilot agent may declare (minimum-tool policy).
TOOL_POLICY = {
    "cohestra-coordinator": {"read", "search", "agent"},
    "cohestra-context-analyst": {"read", "search"},
    "cohestra-software-architect": {"read", "search"},
    "cohestra-implementation-engineer": {"read", "search", "edit", "execute"},
    "cohestra-security-engineer": {"read", "search", "execute"},
    "cohestra-test-engineer": {"read", "search", "edit", "execute"},
    "cohestra-quality-engineer": {"read", "search", "execute"},
    "cohestra-documentation-engineer": {"read", "search", "edit"},
    "cohestra-pattern-writer": {"read", "search", "edit"},
}

COPILOT_DIR = Path("com.github.copilot") / "agents"
CLAUDE_DIR = Path("agents")
COPILOT_SUFFIX = ".agent.md"

# Frontmatter keys that Cohestra Copilot agent files may use.
COPILOT_KEYS = {
    "name",
    "description",
    "tools",
    "agents",
    "user-invocable",
    "disable-model-invocation",
}

# Copilot tool alias -> Claude Code tool names.
TOOL_MAP = {
    "read": ["Read"],
    "search": ["Glob", "Grep"],
    "edit": ["Edit", "Write"],
    "execute": ["Bash"],
    "agent": ["Agent"],
}

# The closed Agent Plugins 1.0.0 manifest schema (plugin.schema.json).
PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PLUGIN_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": PLUGIN_SCHEMA_ID,
    "title": "Agent Plugins Manifest",
    "type": "object",
    "properties": {
        "$schema": {"const": PLUGIN_SCHEMA_ID},
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 64,
            "pattern": r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$",
        },
        "version": {"type": "string"},
        "description": {"type": "string"},
        "author": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "url": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "homepage": {"type": "string"},
        "repository": {"type": "string"},
        "license": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "extensions": {"type": "object", "additionalProperties": {"type": "object"}},
    },
    "required": ["$schema", "name"],
    "additionalProperties": False,
}

# Paths that the repository scan skips.
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", "dist"}


class FrontmatterError(ValueError):
    """Raised when frontmatter is missing or outside the supported YAML subset."""


# --- Files ------------------------------------------------------------------


def iter_repo_files(root: Path):
    """Yield repository files in sorted order. Skip caches, .git, and eval results."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        if parts[:2] == ("evals", "results"):
            continue
        if path.suffix == ".pyc":
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- Frontmatter ------------------------------------------------------------


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body). The body is the exact text after the closing rule."""
    if text.startswith("---\n---\n"):
        return "", text[len("---\n---\n"):]
    if not text.startswith("---\n"):
        raise FrontmatterError("file does not start with a '---' frontmatter line")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise FrontmatterError("frontmatter has no closing '---' line")
    return text[4:end], text[end + len("\n---\n"):]


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?: +(.*))?$")


def _parse_quoted(raw: str) -> tuple[str, str]:
    """Parse a quoted scalar at the start of raw. Return (value, rest)."""
    quote = raw[0]
    out: list[str] = []
    i = 1
    while i < len(raw):
        ch = raw[i]
        if quote == "'":
            if ch == "'":
                if raw[i + 1:i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), raw[i + 1:]
        else:
            if ch == "\\":
                nxt = raw[i + 1:i + 2]
                if nxt not in {'"', "\\", "n", "t"}:
                    raise FrontmatterError(f"unsupported escape '\\{nxt}'")
                out.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                i += 2
                continue
            if ch == '"':
                return "".join(out), raw[i + 1:]
        out.append(ch)
        i += 1
    raise FrontmatterError("quoted value has no closing quote")


def _plain(raw: str, in_flow: bool = False):
    value = raw.strip()
    if value == "":
        raise FrontmatterError("empty value")
    if value[0] in "&*!|>%@`" or value.startswith(("- ", "? ")):
        raise FrontmatterError(f"plain value starts with a YAML indicator: {value!r}")
    if ": " in value or value.endswith(":") or " #" in value:
        raise FrontmatterError(f"plain value needs quotes: {value!r}")
    if in_flow and any(ch in value for ch in "[]{}"):
        raise FrontmatterError(f"flow item needs quotes: {value!r}")
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _split_flow(inner: str) -> list[str]:
    """Split a flow collection body on top-level commas. Respect quotes."""
    items: list[str] = []
    current: list[str] = []
    quote = ""
    i = 0
    while i < len(inner):
        ch = inner[i]
        if quote:
            current.append(ch)
            if quote == '"' and ch == "\\":
                current.append(inner[i + 1:i + 2])
                i += 1
            elif ch == quote:
                if quote == "'" and inner[i + 1:i + 2] == "'":
                    current.append("'")
                    i += 1
                else:
                    quote = ""
        elif ch in "'\"":
            quote = ch
            current.append(ch)
        elif ch == ",":
            items.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    if quote:
        raise FrontmatterError("flow collection has an unclosed quote")
    tail = "".join(current)
    if tail.strip() or items:
        items.append(tail)
    return items


def _scalar(raw: str, in_flow: bool = False):
    raw = raw.strip()
    if raw and raw[0] in "'\"":
        value, rest = _parse_quoted(raw)
        if rest.strip():
            raise FrontmatterError(f"unexpected text after quoted value: {rest.strip()!r}")
        return value
    return _plain(raw, in_flow)


def parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise FrontmatterError("flow list is not closed with ']'")
        return [_scalar(item, True) for item in _split_flow(raw[1:-1])]
    if raw.startswith("{"):
        if not raw.endswith("}"):
            raise FrontmatterError("flow map is not closed with '}'")
        result = {}
        for item in _split_flow(raw[1:-1]):
            key, sep, value = item.partition(":")
            if not sep:
                raise FrontmatterError(f"flow map item has no ':' : {item.strip()!r}")
            key = key.strip()
            if key in result:
                raise FrontmatterError(f"duplicate flow map key '{key}'")
            result[key] = _scalar(value, True)
        return result
    return _scalar(raw)


def parse_frontmatter(text: str) -> dict:
    """Parse the supported YAML subset: one 'key: value' per line, flow lists and maps."""
    values: dict = {}
    for number, line in enumerate(text.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            raise FrontmatterError(
                f"line {number}: indented or continued lines are not supported; "
                "write each key on one line"
            )
        match = _KEY_RE.match(line)
        if not match:
            raise FrontmatterError(f"line {number}: expected 'key: value'")
        key, raw = match.group(1), match.group(2)
        if key in values:
            raise FrontmatterError(f"line {number}: duplicate key '{key}'")
        if raw is None:
            raise FrontmatterError(f"line {number}: key '{key}' has no value")
        try:
            values[key] = parse_value(raw)
        except FrontmatterError as error:
            raise FrontmatterError(f"line {number}: key '{key}': {error}") from None
    return values


def yaml_scalar(value: str) -> str:
    """Return value as a YAML scalar. Add double quotes only when needed."""
    needs_quotes = (
        value != value.strip()
        or value == ""
        or value[0] in "[]{}&*!|>'\"%@`#,-?:"
        or ": " in value
        or value.endswith(":")
        or " #" in value
        or value in {"true", "false", "null", "~"}
        or re.fullmatch(r"-?\d+", value) is not None
    )
    if not needs_quotes:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# --- Agents -----------------------------------------------------------------


@dataclass
class Agent:
    path: Path
    agent_id: str
    meta: dict
    body: str
    text: str


def agent_id_from_path(path: Path) -> str:
    return path.name[: -len(COPILOT_SUFFIX)] if path.name.endswith(COPILOT_SUFFIX) else path.stem


def load_agent(path: Path) -> Agent:
    text = read_text(path)
    frontmatter, body = split_frontmatter(text)
    return Agent(path, agent_id_from_path(path), parse_frontmatter(frontmatter), body, text)


def claude_tools(copilot_tools: list[str]) -> list[str]:
    """Map Copilot tool aliases to Claude Code tool names. Keep order. Remove duplicates."""
    tools: list[str] = []
    for alias in copilot_tools:
        if alias not in TOOL_MAP:
            raise ValueError(f"unsupported Copilot tool alias '{alias}'")
        for tool in TOOL_MAP[alias]:
            if tool not in tools:
                tools.append(tool)
    return tools


def render_claude_agent(agent: Agent) -> str:
    """Render the Claude Code mirror of a Copilot agent. The body stays byte-identical."""
    unknown = sorted(set(agent.meta) - COPILOT_KEYS)
    if unknown:
        raise ValueError(f"{agent.path.name}: unsupported frontmatter keys: {', '.join(unknown)}")
    description = agent.meta.get("description")
    tools = agent.meta.get("tools")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{agent.path.name}: missing description")
    if not isinstance(tools, list):
        raise ValueError(f"{agent.path.name}: tools must be a list")
    return (
        "---\n"
        f"name: {agent.agent_id}\n"
        f"description: {yaml_scalar(description)}\n"
        f"tools: {', '.join(claude_tools(tools))}\n"
        "---\n"
        f"{agent.body}"
    )


def expected_mirrors(root: Path) -> dict[Path, str]:
    """Return {mirror path: expected text} for every Copilot agent file."""
    source = root / COPILOT_DIR
    return {
        root / CLAUDE_DIR / f"{agent_id_from_path(path)}.md": render_claude_agent(load_agent(path))
        for path in sorted(source.glob(f"*{COPILOT_SUFFIX}"))
    }


# --- Minimal JSON Schema evaluator -----------------------------------------


def schema_errors(instance, schema: dict, path: str = "$") -> list[str]:
    """Check instance against the JSON Schema subset that the manifest schema uses."""
    errors: list[str] = []
    kind = schema.get("type")
    checks = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "number": (int, float),
    }
    if kind and not isinstance(instance, checks[kind]):
        return [f"{path}: expected {kind}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']!r}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than {schema['maxLength']} characters")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match pattern {schema['pattern']}")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required field '{key}'")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(schema_errors(value, properties[key], f"{path}.{key}"))
            elif extra is False:
                errors.append(f"{path}: unknown field '{key}'")
            elif isinstance(extra, dict):
                errors.extend(schema_errors(value, extra, f"{path}.{key}"))
    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(schema_errors(item, schema["items"], f"{path}[{index}]"))
    return errors
