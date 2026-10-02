#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "com.github.copilot" / "agents"
TARGET = ROOT / "agents"
TOOL_MAP = {"read": ["Read", "Glob", "Grep"], "search": ["Glob", "Grep"], "agent": ["Agent"], "edit": ["Edit", "Write"], "execute": ["Bash"]}

def parse(text):
    _, frontmatter, body = text.split("---\n", 2)
    values = {}
    for line in frontmatter.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values, body

TARGET.mkdir(exist_ok=True)
for source in sorted(SOURCE.glob("*.agent.md")):
    values, body = parse(source.read_text(encoding="utf-8"))
    raw = values.get("tools", "[]").strip("[]")
    tools = []
    for item in (part.strip() for part in raw.split(",")):
        for tool in TOOL_MAP.get(item, [item] if item else []):
            if tool not in tools: tools.append(tool)
    agent_id = source.name.removesuffix(".agent.md")
    result = "---\n" + f"name: {agent_id}\n" + f"description: {values['description']}\n" + f"tools: {', '.join(tools)}\n" + "---\n" + body
    (TARGET / f"{agent_id}.md").write_text(result, encoding="utf-8")
