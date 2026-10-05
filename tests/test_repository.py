"""Unit tests for the Cohestra repository.

Expected values are written out here on purpose. They do not come from
scripts/cohestra_common.py, so a mistake in that file cannot hide itself.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cohestra_common as common  # noqa: E402
import package  # noqa: E402
import release_notes  # noqa: E402
import sync_claude_agents as sync  # noqa: E402
import validate  # noqa: E402

HAS_BASH = shutil.which("bash") is not None
HAS_YAML = validate.yaml is not None

NAME = "cohestra"
VERSION = "0.1.0"
URL = "https://github.com/mbaic/mb-cohestra-agent-plugin"
COORDINATOR_FILE = "mb-cohestra-coordinator"
SPECIALIST_FILES = [
    "mb-cohestra-context-analyst",
    "mb-cohestra-software-architect",
    "mb-cohestra-implementation-engineer",
    "mb-cohestra-security-engineer",
    "mb-cohestra-test-engineer",
    "mb-cohestra-quality-engineer",
    "mb-cohestra-documentation-engineer",
    "mb-cohestra-pattern-writer",
]
SPECIALIST_NAMES = [
    "mb-Cohestra Context Analyst",
    "mb-Cohestra Software Architect",
    "mb-Cohestra Implementation Engineer",
    "mb-Cohestra Security Engineer",
    "mb-Cohestra Test Engineer",
    "mb-Cohestra Quality Engineer",
    "mb-Cohestra Documentation Engineer",
    "mb-Cohestra Pattern Writer",
]
TOOLS = {
    "mb-cohestra-coordinator": ["read", "search", "agent"],
    "mb-cohestra-context-analyst": ["read", "search"],
    "mb-cohestra-software-architect": ["read", "search"],
    "mb-cohestra-implementation-engineer": ["read", "search", "edit", "execute"],
    "mb-cohestra-security-engineer": ["read", "search", "execute"],
    "mb-cohestra-test-engineer": ["read", "search", "edit", "execute"],
    "mb-cohestra-quality-engineer": ["read", "search", "execute"],
    "mb-cohestra-documentation-engineer": ["read", "search", "edit"],
    "mb-cohestra-pattern-writer": ["read", "search", "edit"],
}
ROOT_MANIFEST_KEYS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
STALE = [
    "multi-agent-review-coordinator", "agent-review-suite", "Review Orchestrator",
    "review-orchestrator", "coordinated software review", "4.0.0", "5.0.0",
    "OWNER/REPOSITORY", "Repository owner",
]
CASE_SENSITIVE = {"OWNER/REPOSITORY", "Repository owner"}
EXEMPT_FROM_STALE = {"scripts/validate.py", "tests/test_repository.py", "tests/run.py"}
README_SECTIONS = [
    "Agents", "How it works", "Capabilities", "Boundaries", "Package", "Install", "Use",
    "Client support", "Validate", "Evaluate", "Update", "Troubleshooting", "Security",
    "Contributing", "License",
]
CASES = [
    "delegates-context-map", "plans-architecture-without-edits", "implements-focused-change",
    "delegates-security-review", "improves-tests", "updates-documentation", "writes-from-pattern",
    "completes-engineering-task", "reviews-without-edits", "unrelated-request",
]

GOOD_FILES = {
    "implements-focused-change": {
        "src/slugify.js": "export function slugify(text) {\n  return text.toLowerCase();\n}\n",
        "test/slugify.test.js": "import { slugify } from '../src/slugify.js';\n",
    },
    "improves-tests": {
        "test/retry-timeout.test.js": "// timeout and retry\nimport '../src/retry.js';\n",
    },
    "updates-documentation": {
        "docs/setup.md": "# Setup\n| PORT | 3000 |\n| RATE_LIMIT_MAX | 100 |\n| RATE_LIMIT_WINDOW_SECONDS | 60 |\n",
    },
    "writes-from-pattern": {
        "src/handlers/get-invoice.js": "export function getInvoice(id) {\n  return db.find('invoices', id);\n}\n",
    },
    "completes-engineering-task": {
        "src/order.js": "throw new RangeError('quantity');\n",
        "test/order-quantity.test.js": "assert.throws(f, RangeError);\n",
        "docs/orders.md": "The quantity must be positive. Otherwise a RangeError occurs.\n",
    },
}
GOOD_MESSAGE = {
    "delegates-context-map": "src/login.js calls src/token.js. Test: test/login.test.js.",
    "plans-architecture-without-edits": "Add an interface in src/storage.js. Plan a rollback.",
    "delegates-security-review": "SQL injection. Use a parameterized query.",
    "reviews-without-edits": "SQL injection and no authorization check for the requester.",
    "unrelated-request": "4",
}
MARKER_GRADERS = ("unchanged", "keeps-existing-text")


def copy_repo(destination: Path) -> Path:
    target = destination / "repo"
    shutil.copytree(
        ROOT, target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "dist", "results", "*.pyc"),
    )
    return target


def text_files():
    return [p for p in common.iter_repo_files(ROOT)]


def first_frontmatter(path: Path) -> dict:
    raw, _ = common.split_frontmatter(path.read_text(encoding="utf-8"))
    return common.parse_frontmatter(raw)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.root = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.market = json.loads((ROOT / ".github/plugin/marketplace.json").read_text(encoding="utf-8"))

    def test_root_manifest_values(self):
        self.assertEqual(self.root["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(self.root["name"], NAME)
        self.assertEqual(self.root["version"], VERSION)
        self.assertEqual(self.root["license"], "MIT")
        self.assertEqual(self.root["author"], {"name": "Milos Baic", "url": "https://github.com/mbaic"})
        self.assertEqual(self.root["homepage"], URL)
        self.assertEqual(self.root["repository"], URL)

    def test_root_manifest_uses_only_allowed_keys(self):
        self.assertLessEqual(set(self.root), ROOT_MANIFEST_KEYS)

    def test_root_manifest_passes_local_schema(self):
        self.assertEqual(common.schema_errors(self.root, common.PLUGIN_SCHEMA), [])

    def test_all_manifest_versions_agree(self):
        self.assertEqual(self.claude["version"], VERSION)
        self.assertEqual(self.market["metadata"]["version"], VERSION)
        self.assertEqual(self.market["plugins"][0]["version"], VERSION)
        self.assertEqual(self.claude["name"], NAME)

    def test_marketplace_points_to_the_repository_root(self):
        self.assertEqual(self.market["name"], "mb-cohestra-agent-plugin")
        self.assertEqual(self.market["owner"]["name"], "Milos Baic")
        self.assertEqual(len(self.market["plugins"]), 1)
        self.assertEqual(self.market["plugins"][0]["name"], NAME)
        self.assertEqual(self.market["plugins"][0]["source"], "./")

    def test_readme_identity(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# Cohestra\n\n**Coordinated software engineering.**\n"))
        self.assertNotIn("Coordinated software review", readme)

    def test_changelog_starts_with_the_release_section(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [0.1.0] - 2026-10-02", text)
        self.assertIn("### Added", text)

    def test_license_names_the_author(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", text)
        self.assertIn("Copyright (c) 2026 Milos Baic", text)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agents = {
            path.name[: -len(".agent.md")]: common.load_agent(path)
            for path in sorted((ROOT / "com.github.copilot/agents").glob("*.agent.md"))
        }

    def test_exactly_nine_agent_files(self):
        self.assertEqual(sorted(self.agents), sorted([COORDINATOR_FILE] + SPECIALIST_FILES))

    def test_file_name_and_display_name_agree(self):
        for file_id, agent in self.agents.items():
            # File mb-cohestra-test-engineer.agent.md has the display name "mb-Cohestra Test Engineer".
            expected = "mb-" + " ".join(word.capitalize() for word in file_id.split("-")[1:])
            self.assertEqual(agent.meta["name"], expected, file_id)

    def test_exactly_one_visible_agent(self):
        visible = [a.meta["name"] for a in self.agents.values() if a.meta.get("user-invocable", True) is not False]
        self.assertEqual(visible, ["mb-Cohestra Coordinator"])

    def test_specialists_are_hidden_and_callable(self):
        for file_id in SPECIALIST_FILES:
            meta = self.agents[file_id].meta
            self.assertIs(meta["user-invocable"], False, file_id)
            self.assertIs(meta["disable-model-invocation"], False, file_id)

    def test_specialists_cannot_delegate(self):
        for file_id in SPECIALIST_FILES:
            meta = self.agents[file_id].meta
            self.assertEqual(meta["agents"], [], file_id)
            self.assertNotIn("agent", meta["tools"], file_id)

    def test_coordinator_flags_and_allowlist(self):
        meta = self.agents[COORDINATOR_FILE].meta
        self.assertIs(meta["user-invocable"], True)
        self.assertIs(meta["disable-model-invocation"], True)
        self.assertEqual(sorted(meta["agents"]), sorted(SPECIALIST_NAMES))
        self.assertEqual(len(meta["agents"]), 8)
        self.assertNotIn("mb-Cohestra Coordinator", meta["agents"])

    def test_no_target_and_no_model(self):
        for file_id, agent in self.agents.items():
            self.assertNotIn("target", agent.meta, file_id)
            self.assertNotIn("model", agent.meta, file_id)
            self.assertNotRegex(agent.text.split("\n---\n", 1)[0], r"(?m)^target:", file_id)

    def test_only_supported_frontmatter_fields(self):
        allowed = {"name", "description", "tools", "agents", "user-invocable", "disable-model-invocation"}
        for file_id, agent in self.agents.items():
            self.assertLessEqual(set(agent.meta), allowed, file_id)

    def test_tool_policy(self):
        for file_id, agent in self.agents.items():
            self.assertEqual(agent.meta["tools"], TOOLS[file_id], file_id)

    def test_specialist_contract_and_handback(self):
        for file_id in SPECIALIST_FILES:
            body = self.agents[file_id].body
            for line in validate.CONTRACT_LINES:
                self.assertIn(f"- {line}", body, file_id)
            for field in validate.HANDBACK_FIELDS:
                self.assertRegex(body, rf"(?m)^{re.escape(field)}$")

    def test_coordinator_prompt_content(self):
        body = self.agents[COORDINATOR_FILE].body
        for number in range(1, 16):
            self.assertRegex(body, rf"(?m)^{number}\. ")
        for line in validate.FINAL_RESPONSE:
            self.assertRegex(body, rf"(?m)^{re.escape(line)}$")
        for name in SPECIALIST_NAMES:
            self.assertIn(name, body)

    def test_pattern_writer_is_kept_and_limited(self):
        agent = self.agents["mb-cohestra-pattern-writer"]
        self.assertIn("low-risk", agent.meta["description"])
        self.assertIn("architecture, security, concurrency, migration", agent.body)

    def test_files_end_with_one_newline(self):
        for agent in self.agents.values():
            self.assertTrue(agent.text.endswith("\n") and not agent.text.endswith("\n\n"), agent.path.name)

    def test_prompts_use_agreed_terms(self):
        for agent in self.agents.values():
            self.assertNotRegex(agent.body, r"(?i)\bworker", agent.path.name)
            self.assertNotRegex(agent.body, r"(?i)\bsubagent", agent.path.name)


class MirrorTests(unittest.TestCase):
    def test_mirrors_are_in_sync(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sync.main(["--check"]), 0)

    def test_mirror_files_and_frontmatter(self):
        names = sorted(p.name for p in (ROOT / "agents").glob("*"))
        self.assertEqual(names, sorted(f"{x}.md" for x in [COORDINATOR_FILE] + SPECIALIST_FILES))
        for path in (ROOT / "agents").glob("*.md"):
            meta = first_frontmatter(path)
            self.assertEqual(set(meta), {"name", "description", "tools"}, path.name)
            self.assertEqual(meta["name"], path.stem)

    def test_tool_mapping(self):
        self.assertEqual(first_frontmatter(ROOT / "agents/mb-cohestra-coordinator.md")["tools"], "Read, Glob, Grep, Agent")
        self.assertEqual(
            first_frontmatter(ROOT / "agents/mb-cohestra-implementation-engineer.md")["tools"],
            "Read, Glob, Grep, Edit, Write, Bash",
        )
        self.assertEqual(first_frontmatter(ROOT / "agents/mb-cohestra-context-analyst.md")["tools"], "Read, Glob, Grep")

    def test_mirror_keeps_the_prompt_body(self):
        for path in (ROOT / "com.github.copilot/agents").glob("*.agent.md"):
            _, source_body = common.split_frontmatter(path.read_text(encoding="utf-8"))
            mirror = ROOT / "agents" / (path.name[: -len(".agent.md")] + ".md")
            _, mirror_body = common.split_frontmatter(mirror.read_text(encoding="utf-8"))
            self.assertEqual(source_body, mirror_body, path.name)

    def test_check_fails_on_a_stale_mirror_and_write_repairs_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            mirror = repo / "agents/mb-cohestra-test-engineer.md"
            mirror.write_text(mirror.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.main(["--check", "--root", str(repo)]), 1)
                self.assertEqual(sync.main(["--root", str(repo)]), 0)
                self.assertEqual(sync.main(["--check", "--root", str(repo)]), 0)

    def test_check_fails_on_a_missing_and_an_orphan_mirror(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            (repo / "agents/mb-cohestra-pattern-writer.md").unlink()
            (repo / "agents/old-agent.md").write_text("---\nname: old-agent\n---\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(sync.main(["--check", "--root", str(repo)]), 1)
            self.assertIn("missing mirror", out.getvalue())
            self.assertIn("orphan mirror", out.getvalue())

    def test_sync_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            for path in (repo / "agents").glob("*.md"):
                path.unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                sync.main(["--root", str(repo)])
            first = {p.name: p.read_bytes() for p in (repo / "agents").glob("*.md")}
            with contextlib.redirect_stdout(io.StringIO()):
                sync.main(["--root", str(repo)])
            second = {p.name: p.read_bytes() for p in (repo / "agents").glob("*.md")}
            self.assertEqual(first, second)
            self.assertEqual(len(first), 9)

    def test_sync_rejects_an_unknown_field_and_an_unknown_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            source = repo / "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md"
            text = source.read_text(encoding="utf-8")
            source.write_text(text.replace("agents: []\n", "agents: []\nhandoffs: [x]\n", 1), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.main(["--check", "--root", str(repo)]), 1)
            source.write_text(text.replace("tools: [read, search, edit, execute]", "tools: [read, teleport]"), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.main(["--check", "--root", str(repo)]), 1)


class SkillTests(unittest.TestCase):
    def test_skill_name_matches_directory(self):
        folders = [p.name for p in (ROOT / "skills").iterdir() if p.is_dir()]
        self.assertEqual(folders, ["cohestra-engineering"])
        meta = first_frontmatter(ROOT / "skills/cohestra-engineering/SKILL.md")
        self.assertEqual(meta["name"], "cohestra-engineering")
        self.assertTrue(meta["description"])
        self.assertLessEqual(set(meta), {"name", "description"})

    def test_skill_covers_required_topics(self):
        text = (ROOT / "skills/cohestra-engineering/SKILL.md").read_text(encoding="utf-8")
        for heading in ("Classify the task", "Find repository instructions", "Search before you read",
                        "Delegate within bounds", "Require evidence", "Edit and run commands safely",
                        "Test and document", "Final response"):
            self.assertIn(f"## {heading}", text)


class ForbiddenComponentTests(unittest.TestCase):
    def test_no_hooks(self):
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            self.assertNotEqual(path.name, "hooks", path)
            self.assertNotEqual(path.name, "hooks.json", path)

    def test_no_mcp_configuration(self):
        for relative in ("mcp.json", ".mcp.json", ".github/mcp.json", "com.github.copilot/mcp.json"):
            self.assertFalse((ROOT / relative).exists(), relative)
        for relative in ("plugin.json", ".claude-plugin/plugin.json"):
            data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertFalse({"hooks", "mcpServers", "mcp-servers"} & set(data), relative)

    def test_no_binary_files(self):
        for path in text_files():
            self.assertNotIn(b"\x00", path.read_bytes(), path)


class HygieneTests(unittest.TestCase):
    def test_text_files_end_with_one_newline_and_use_lf(self):
        for path in text_files():
            data = path.read_bytes()
            if not data:
                continue
            self.assertTrue(data.endswith(b"\n"), f"missing final newline: {path}")
            self.assertFalse(data.endswith(b"\n\n"), f"extra blank line at end: {path}")
            self.assertNotIn(b"\r", data, f"carriage return: {path}")

    def test_no_stale_names_or_placeholders(self):
        for path in text_files():
            relative = path.relative_to(ROOT).as_posix()
            if relative in EXEMPT_FROM_STALE:
                continue
            text = path.read_text(encoding="utf-8")
            for stale in STALE:
                # The placeholders are capitalized. Ordinary prose such as "the repository owner" is fine.
                haystack, needle = (text, stale) if stale in CASE_SENSITIVE else (text.lower(), stale.lower())
                self.assertNotIn(needle, haystack, f"{relative} has {stale!r}")

    def test_repository_name_is_consistent(self):
        # The GitHub repository is mb-cohestra-agent-plugin. The plugin ID stays cohestra.
        for path in text_files():
            relative = path.relative_to(ROOT).as_posix()
            if relative in EXEMPT_FROM_STALE:
                continue
            text = path.read_text(encoding="utf-8")
            for repo in re.findall(r"github\.com/mbaic/([A-Za-z0-9._-]+)", text):
                self.assertEqual(repo, "mb-cohestra-agent-plugin", relative)
            self.assertNotRegex(text, r"(?<!mb-)cohestra-agent-plugin", relative)
            self.assertNotRegex(text, r"mbaic/(?!mb-cohestra-agent-plugin)cohestra", relative)

    def test_install_commands_use_the_repository_name_and_the_plugin_id(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("copilot plugin marketplace add mbaic/mb-cohestra-agent-plugin", readme)
        self.assertIn("copilot plugin install cohestra@mb-cohestra-agent-plugin", readme)
        market = json.loads((ROOT / ".github/plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["name"], "mb-cohestra-agent-plugin")
        self.assertEqual(market["plugins"][0]["name"], "cohestra")

    def test_gitignore_covers_generated_output(self):
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in ("evals/results/", "dist/", "__pycache__/"):
            self.assertIn(entry, lines)

    def test_full_validator_passes(self):
        report, checked = validate.run(ROOT)
        self.assertEqual(report.errors, [])
        self.assertGreater(checked, 100)

    def test_required_files_exist(self):
        for relative in validate.REQUIRED_FILES:
            self.assertTrue((ROOT / relative).is_file(), relative)


class ReadmeTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_opening_copy(self):
        self.assertTrue(self.text.startswith(
            "# Cohestra\n\n**Coordinated software engineering.**\n\n"
            "Cohestra coordinates specialist AI agents for software engineering work. "
            "You use one visible agent: **mb-Cohestra Coordinator**.\n\n"
            "The coordinator defines the task. It selects the required specialists. "
            "It checks their work. It returns one result.\n"
        ))

    def test_scope_statement(self):
        self.assertIn(
            "> Cohestra can plan, build, test, secure, document, and assess software. "
            "Code review is one capability. It is not the product boundary.",
            self.text,
        )

    def test_required_sections_in_order(self):
        headings = re.findall(r"(?m)^## (.+)$", self.text)
        positions = [headings.index(name) for name in README_SECTIONS]
        self.assertEqual(positions, sorted(positions))

    def test_install_subsections(self):
        for title in ("VS Code", "VS Code local development", "GitHub Copilot CLI", "GitHub Copilot app", "Claude Code"):
            self.assertRegex(self.text, rf"(?m)^### {re.escape(title)}$")

    def test_install_commands(self):
        for needle in (
            "copilot plugin marketplace add mbaic/mb-cohestra-agent-plugin",
            "copilot plugin install cohestra@mb-cohestra-agent-plugin",
            "chat.plugins.enabled",
            "Chat: Install Plugin From Source",
            "https://github.com/mbaic/mb-cohestra-agent-plugin",
            '"/absolute/path/to/mb-cohestra-agent-plugin": true',
            "chat.pluginLocations",
        ):
            self.assertIn(needle, self.text)

    def test_usage_examples(self):
        # The examples use Business Central AL development.
        for prompt in (
            'Add a Customer Rating field to the Customer table with a table extension. Show it on the Customer Card with a page extension. Use the object ID range from app.json and the name prefix of the other objects. Add an AL test and update the documentation.',
            'Plan the move of this extension from Business Central on-premises to SaaS. List the AL code that SaaS does not allow, such as DotNet variables and file system access. Do not edit files.',
            'Find the cause of the failing test codeunit for posting a sales invoice. The error says that the posting date is not within the range of allowed posting dates. Make the smallest safe correction. Run the related tests.',
            'Check the current changes for correctness, performance, permissions, and missing tests. Look for missing SetLoadFields calls, FindSet calls inside loops, hard-coded text, and objects that have no permission set entry. Do not edit files.',
            'Add AL tests for the credit limit check on the sales order. Use the Library - Sales and Library Assert codeunits. Cover a customer under the limit, over the limit, and blocked. Do not change production code.',
            'Update the README for the new setup page. List each field, its default value, and the permission set that grants access. Check each field name against the page object.',
        ):
            self.assertIn(prompt, self.text)

    def test_more_prompts_use_business_central_terms(self):
        use = self.text.split("\n## Use\n", 1)[1].split("\n## Client support", 1)[0]
        for term in ("Business Central", "AL ", "codeunit", "table extension", "permission set", "SetLoadFields",
                     "event subscribers", "AL-Go for GitHub", "SaaS", "FlowField"):
            self.assertIn(term, use)

    def test_readme_gives_enough_prompt_examples(self):
        use = self.text.split("\n## Use\n", 1)[1].split("\n## Client support", 1)[0]
        blocks = re.findall(r"```text\n(.+?)\n```", use, re.DOTALL)
        self.assertGreaterEqual(len(blocks), 16)
        self.assertIn("### More prompts", use)
        self.assertIn("### Tips for good prompts", use)
        self.assertIn("Do not edit files", use)
        self.assertIn("Use the mb-Cohestra Coordinator to", use)

    def test_accurate_boundaries(self):
        self.assertIn("The plugin is not read-only.", self.text)
        self.assertNotRegex(self.text, r"(?i)fully read-only")
        self.assertIn("The package adds no telemetry code.", self.text)
        self.assertNotRegex(self.text, r"(?i)no telemetry\b(?! code)")
        self.assertIn("AI output can be wrong.", self.text)

    def test_client_support_table_lists_every_client(self):
        for client in ("VS Code Copilot Chat", "VS Code Local and Copilot sessions", "GitHub Copilot CLI",
                       "GitHub Copilot app", "Claude Code"):
            self.assertIn(f"| {client} |", self.text)

    def test_all_nine_agents_in_the_table(self):
        for name in ["mb-Cohestra Coordinator"] + SPECIALIST_NAMES:
            self.assertIn(f"| {name} |", self.text)

    def test_relative_links_resolve(self):
        for target in re.findall(r"\]\((?!https?://|#)([^)#]+)", self.text):
            self.assertTrue((ROOT / target).exists(), target)


class EvalTests(unittest.TestCase):
    def cases(self):
        return [p.parent for p in sorted((ROOT / "evals").glob("*/prompt.md"))]

    def test_required_cases_exist(self):
        self.assertEqual(sorted(p.name for p in self.cases()), sorted(CASES))

    def test_every_case_has_graders_limits_and_a_deterministic_grader(self):
        for case in self.cases():
            graders = sorted((case / "graders").glob("*.md"))
            self.assertTrue(graders, case.name)
            kinds = [first_frontmatter(g)["type"] for g in graders]
            self.assertTrue(set(kinds) - {"llm", "baseline"}, f"{case.name} has only LLM graders")
            meta = first_frontmatter(case / "prompt.md")
            for key in ("runs", "max_turns", "timeout_seconds", "allowed_tools"):
                self.assertIn(key, meta, case.name)
            self.assertEqual(meta["plugins"], ["../.."])
            self.assertNotIn("Bash", meta["allowed_tools"], case.name)

    def test_agent_matches_use_the_plugin_namespace(self):
        seen = 0
        for grader in (ROOT / "evals").glob("*/graders/*.md"):
            meta = first_frontmatter(grader)
            if meta.get("tool") == "Agent" and meta.get("input_match"):
                seen += 1
                self.assertTrue(meta["input_match"].startswith("cohestra:"), grader)
                for token in re.findall(r"(?:mb-)?cohestra-[a-z]+(?:-[a-z]+)*", meta["input_match"]):
                    self.assertIn(token, [COORDINATOR_FILE] + SPECIALIST_FILES, grader)
        self.assertGreaterEqual(seen, 8)

    def test_read_only_cases_carry_the_smoke_tag(self):
        for case in self.cases():
            meta = first_frontmatter(case / "prompt.md")
            needs_edit = "edit" in meta["tags"]
            self.assertEqual(needs_edit, "smoke" not in meta["tags"], case.name)

    @unittest.skipUnless(HAS_BASH, "bash is not available")
    def test_fixture_scripts_have_valid_syntax(self):
        for script in (ROOT / "evals").glob("*/fixture.sh"):
            result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"{script}: {result.stderr}")

    @unittest.skipUnless(HAS_BASH, "bash is not available")
    def test_deterministic_graders_reject_the_fixture_and_accept_a_good_result(self):
        for case in self.cases():
            with tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                script = case / "fixture.sh"
                if script.exists():
                    subprocess.run(["bash", str(script)], cwd=work, check=True, capture_output=True,
                                   env={"PATH": "/usr/bin:/bin", "HOME": str(work)})
                before = self.grade(case, work, "", [])
                good = GOOD_FILES.get(case.name, {})
                for relative, content in good.items():
                    (work / relative).parent.mkdir(parents=True, exist_ok=True)
                    (work / relative).write_text(content, encoding="utf-8")
                after = self.grade(case, work, GOOD_MESSAGE.get(case.name, ""), list(good))
                for name, passed in after.items():
                    self.assertTrue(passed, f"{case.name}/{name} rejects a correct result")
                    if not name.endswith(MARKER_GRADERS):
                        self.assertFalse(before[name], f"{case.name}/{name} passes on the untouched fixture")

    def test_plan_grader_accepts_equivalent_design_words_and_still_rejects_a_thin_answer(self):
        meta = first_frontmatter(ROOT / "evals/plans-architecture-without-edits/graders/plan-content.md")
        flags = re.IGNORECASE
        good = "Put a thin facade over src/storage.js and keep local files as a fallback until the copy is verified."
        self.assertIsNotNone(re.search(meta["pattern"], good, flags))
        for thin in ("Move the files to object storage.", "Use an interface in src/storage.js.", "Plan a rollback for src/storage.js."):
            self.assertIsNone(re.search(meta["pattern"], thin, flags), thin)

    @staticmethod
    def grade(case: Path, work: Path, last_message: str, created: list[str]) -> dict[str, bool]:
        results = {}
        for grader in sorted((case / "graders").glob("*.md")):
            meta = first_frontmatter(grader)
            if meta["type"] == "regex":
                target = meta.get("target", "last_message")
                if isinstance(target, dict):
                    path = work / target["path"]
                    text = path.read_text(encoding="utf-8") if path.exists() else ""
                else:
                    text = last_message
                flags = re.IGNORECASE if meta.get("flags") == "i" else 0
                results[grader.stem] = re.search(meta["pattern"], text, flags) is not None
            elif meta["type"] == "file_exists":
                results[grader.stem] = any(Path(p).match(meta["path"]) for p in created)
        return results


class WorkflowTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")

    def test_validate_runs_on_push_and_pull_request(self):
        text = self.read("validate.yml")
        self.assertRegex(text, r"(?m)^  push:")
        self.assertRegex(text, r"(?m)^  pull_request:")
        for step in ("sync_claude_agents.py --check", "scripts/validate.py", "tests/run.py", "bash -n"):
            self.assertIn(step, text)

    def test_eval_is_manual_and_gated(self):
        text = self.read("eval.yml")
        self.assertRegex(text, r"(?m)^  workflow_dispatch:")
        for trigger in ("pull_request", "pull_request_target", "  push:", "schedule:"):
            self.assertNotIn(trigger, text.split("jobs:", 1)[0])
        for flag in ("--trust-plugin", "--scaffold", "--json", "--no-publish", "--threshold",
                     "--max-cost-usd", "--model", "--judge-model"):
            self.assertIn(flag, text)
        self.assertIn("ANTHROPIC_API_KEY", text)
        self.assertIn("upload-artifact", text)
        # The cases run main thread -> coordinator -> specialist. That needs a spawn depth of 2 or more.
        self.assertRegex(text, r"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH: '[3-9]'")
        # The API key reaches only the steps that need it, not the whole job.
        self.assertNotRegex(text.split("jobs:", 1)[1].split("steps:", 1)[0], "ANTHROPIC_API_KEY")
        self.assertNotIn("Bash", text.split("--allow-tools", 1)[1].split("\n", 1)[0])

    def test_release_is_manual_and_checks_before_tagging(self):
        text = self.read("release.yml")
        self.assertRegex(text, r"(?m)^  workflow_dispatch:")
        self.assertNotRegex(text.split("jobs:", 1)[0], r"(?m)^  (push|pull_request|schedule):")
        self.assertIn("default: '0.1.0'", text)
        self.assertLess(text.index("Validate the package"), text.index("Create the tag"))
        self.assertLess(text.index("Run the unit tests"), text.index("Create the tag"))
        self.assertLess(text.index("Build the archive"), text.index("Create the tag"))
        self.assertIn("mb-cohestra-agent-plugin-v", text)
        self.assertIn(".sha256", text)

    @unittest.skipUnless(HAS_YAML, "PyYAML is not installed")
    def test_workflows_parse_and_set_permissions(self):
        for name in ("validate.yml", "eval.yml", "release.yml"):
            doc = validate.yaml.safe_load(self.read(name))
            self.assertIn("permissions", doc, name)
            self.assertIn("jobs", doc, name)
        self.assertEqual(validate.triggers(validate.yaml.safe_load(self.read("release.yml"))), {"workflow_dispatch"})
        self.assertEqual(validate.triggers(validate.yaml.safe_load(self.read("eval.yml"))), {"workflow_dispatch"})


class FrontmatterParserTests(unittest.TestCase):
    def test_parses_the_supported_subset(self):
        meta = common.parse_frontmatter(
            'name: Example Agent\ntools: [read, search]\nagents: ["A B", \'C\']\nflag: true\nn: 3\nempty: []\n'
            "pattern: 'a''b'\ntarget: { source: file, path: x/y.js }\n"
        )
        self.assertEqual(meta["name"], "Example Agent")
        self.assertEqual(meta["tools"], ["read", "search"])
        self.assertEqual(meta["agents"], ["A B", "C"])
        self.assertIs(meta["flag"], True)
        self.assertEqual(meta["n"], 3)
        self.assertEqual(meta["empty"], [])
        self.assertEqual(meta["pattern"], "a'b")
        self.assertEqual(meta["target"], {"source": "file", "path": "x/y.js"})

    def test_rejects_invalid_frontmatter(self):
        for bad in ("a: 1\na: 2\n", "a: [x\n", "a: b: c\n", "a:\n", "  a: 1\n", 'a: "x\n', "a: [x y: z]\n", "- item\n"):
            with self.assertRaises(common.FrontmatterError, msg=bad):
                common.parse_frontmatter(bad)

    def test_split_frontmatter(self):
        self.assertEqual(common.split_frontmatter("---\na: 1\n---\nbody\n"), ("a: 1", "body\n"))
        self.assertEqual(common.split_frontmatter("---\n---\nbody\n"), ("", "body\n"))
        for bad in ("no frontmatter\n", "---\na: 1\n"):
            with self.assertRaises(common.FrontmatterError):
                common.split_frontmatter(bad)

    def test_yaml_scalar_quotes_only_when_needed(self):
        self.assertEqual(common.yaml_scalar("Plain text. With a period, and a comma."), "Plain text. With a period, and a comma.")
        for tricky in ("has: colon", "has #hash", "true", "12", "-lead", ' padded', 'say "hi"'):
            quoted = common.yaml_scalar(tricky)
            self.assertEqual(common.parse_value(quoted), tricky)

    @unittest.skipUnless(HAS_YAML, "PyYAML is not installed")
    def test_built_in_parser_agrees_with_pyyaml_on_every_frontmatter_block(self):
        count = 0
        for path in text_files():
            if path.suffix != ".md":
                continue
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                continue
            raw, _ = common.split_frontmatter(text)
            self.assertEqual(validate.yaml.safe_load(raw) or {}, common.parse_frontmatter(raw), path)
            count += 1
        self.assertGreater(count, 60)


class SchemaTests(unittest.TestCase):
    base = {"$schema": common.PLUGIN_SCHEMA_ID, "name": "cohestra"}

    def errors(self, **extra):
        return common.schema_errors({**self.base, **extra}, common.PLUGIN_SCHEMA)

    def test_accepts_the_minimal_manifest(self):
        self.assertEqual(self.errors(), [])

    def test_rejects_unknown_top_level_field(self):
        self.assertTrue(self.errors(hooks="x"))
        self.assertTrue(self.errors(agents="agents/"))

    def test_rejects_bad_names(self):
        for bad in ("Cohestra", "-cohestra", "co--hestra", "co..hestra", "", "x" * 65):
            self.assertTrue(common.schema_errors({**self.base, "name": bad}, common.PLUGIN_SCHEMA), bad)

    def test_author_object_is_closed(self):
        self.assertTrue(self.errors(author={"name": "A", "twitter": "x"}))
        self.assertEqual(self.errors(author={"name": "A", "url": "https://x.example"}), [])

    def test_requires_schema_and_name(self):
        self.assertTrue(common.schema_errors({"name": "x"}, common.PLUGIN_SCHEMA))
        self.assertTrue(common.schema_errors({"$schema": common.PLUGIN_SCHEMA_ID}, common.PLUGIN_SCHEMA))
        self.assertTrue(common.schema_errors({"$schema": "https://example.invalid/x", "name": "x"}, common.PLUGIN_SCHEMA))

    def test_online_check_warns_and_does_not_fail_when_the_network_is_down(self):
        report = validate.Report()
        with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
            validate.check_online_schema(report, {**self.base})
        self.assertEqual(report.errors, [])
        self.assertTrue(any("live schema check unavailable" in w for w in report.warnings))

    def test_online_check_fails_on_a_manifest_that_the_live_schema_rejects(self):
        live = {**common.PLUGIN_SCHEMA, "properties": {**common.PLUGIN_SCHEMA["properties"], "name": {"type": "string", "maxLength": 3}}}

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch("urllib.request.urlopen", return_value=Response(json.dumps(live).encode())):
            report = validate.Report()
            validate.check_online_schema(report, {**self.base})
        self.assertTrue(report.errors)


class ValidatorNegativeTests(unittest.TestCase):
    """Each test copies the repository, adds one defect, and checks the validator rejects it."""

    def run_mutated(self, mutate, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            mutate(repo)
            report, _ = validate.run(repo, **kwargs)
            return report

    def assertRejects(self, mutate, expected: str, **kwargs):
        report = self.run_mutated(mutate, **kwargs)
        self.assertTrue(report.errors, "the validator accepted a defect")
        self.assertTrue(any(expected in error for error in report.errors), f"{expected!r} not in {report.errors}")

    @staticmethod
    def edit(repo: Path, relative: str, old: str, new: str):
        path = repo / relative
        text = path.read_text(encoding="utf-8")
        assert old in text, (relative, old)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_untouched_copy_passes(self):
        self.assertEqual(self.run_mutated(lambda repo: None).errors, [])

    def test_visible_specialist(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "user-invocable: false", "user-invocable: true"),
            "exactly one Copilot agent must be visible",
        )

    def test_specialist_without_the_visibility_field_is_visible_by_default(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "user-invocable: false\n", ""),
            "exactly one Copilot agent must be visible",
        )

    def test_no_visible_agent(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-coordinator.agent.md", "user-invocable: true", "user-invocable: false"),
            "exactly one Copilot agent must be visible",
        )

    def test_visible_agent_with_the_wrong_name(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-coordinator.agent.md", "name: mb-Cohestra Coordinator", "name: Coordinator"),
            "name must be 'mb-Cohestra Coordinator'",
        )

    def test_blocked_specialist(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "disable-model-invocation: false", "disable-model-invocation: true"),
            "must set disable-model-invocation: false",
        )

    def test_delegating_specialist(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "agents: []", 'agents: ["mb-Cohestra Pattern Writer"]'),
            "cannot delegate",
        )

    def test_specialist_with_the_agent_tool(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-context-analyst.agent.md", "tools: [read, search]", "tools: [read, search, agent]"),
            "tools exceed the policy",
        )

    def test_coordinator_delegation_outside_the_roster(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-coordinator.agent.md", '"mb-Cohestra Pattern Writer"]', '"mb-Cohestra Pattern Writer", "Rogue Agent"]'),
            "delegation outside the Cohestra roster",
        )

    def test_coordinator_allowlist_missing_a_specialist(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-coordinator.agent.md", ', "mb-Cohestra Pattern Writer"]', "]"),
            "allowlist is missing specialists",
        )

    def test_coordinator_with_edit_tools(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-coordinator.agent.md", "tools: [read, search, agent]", "tools: [read, search, agent, edit]"),
            "tools exceed the policy",
        )

    def test_target_field_is_rejected(self):
        for value in ("vscode", "github-copilot"):
            with self.subTest(value=value):
                self.assertRejects(
                    lambda r, v=value: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "agents: []\n", f"agents: []\ntarget: {v}\n"),
                    "'target' is not allowed",
                )

    def test_model_field_is_rejected(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "agents: []\n", "agents: []\nmodel: some-model\n"),
            "'model' is not allowed",
        )

    def test_missing_agent_file(self):
        self.assertRejects(
            lambda r: (r / "com.github.copilot/agents/mb-cohestra-pattern-writer.agent.md").unlink(),
            "missing agent file",
        )

    def test_invalid_frontmatter(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "tools: [read, search, edit, execute]", "tools: [read, search"),
            "invalid YAML frontmatter",
        )

    def test_specialist_contract_line_removed(self):
        self.assertRejects(
            lambda r: self.edit(r, "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md", "- Do not invoke another agent.\n", ""),
            "specialist contract line is missing",
        )

    def test_stale_claude_mirror(self):
        self.assertRejects(
            lambda r: self.edit(r, "agents/mb-cohestra-test-engineer.md", "# Role", "# Role changed"),
            "differs from its Copilot source",
        )

    def test_copilot_only_field_in_a_mirror(self):
        self.assertRejects(
            lambda r: self.edit(r, "agents/mb-cohestra-test-engineer.md", "tools:", "user-invocable: false\ntools:"),
            "Copilot-only or unsupported field",
        )

    def test_hooks_directory(self):
        def mutate(repo):
            (repo / "com.github.copilot/hooks").mkdir(parents=True)
            (repo / "com.github.copilot/hooks/hooks.json").write_text("{}\n", encoding="utf-8")
        self.assertRejects(mutate, "forbidden component")

    def test_hook_file_at_the_root(self):
        self.assertRejects(lambda r: (r / "hooks.json").write_text("{}\n", encoding="utf-8"), "forbidden component")

    def test_mcp_configuration_files(self):
        for name in ("mcp.json", ".mcp.json"):
            with self.subTest(name=name):
                self.assertRejects(lambda r, n=name: (r / n).write_text("{}\n", encoding="utf-8"), "forbidden component")

    def test_manifest_with_a_mcp_key(self):
        self.assertRejects(
            lambda r: self.edit(r, ".claude-plugin/plugin.json", '"license": "MIT"', '"license": "MIT",\n  "mcpServers": {}'),
            "forbidden key",
        )

    def test_manifest_with_an_unknown_top_level_field(self):
        self.assertRejects(
            lambda r: self.edit(r, "plugin.json", '"license": "MIT"', '"license": "MIT",\n  "agents": "agents/"'),
            "unknown field 'agents'",
        )

    def test_wrong_manifest_name(self):
        self.assertRejects(lambda r: self.edit(r, "plugin.json", '"name": "cohestra"', '"name": "other"'), "'name' must be 'cohestra'")

    def test_wrong_manifest_version(self):
        self.assertRejects(lambda r: self.edit(r, "plugin.json", '"version": "0.1.0"', '"version": "0.2.0"'), "'version' must be")

    def test_wrong_claude_manifest_version(self):
        self.assertRejects(lambda r: self.edit(r, ".claude-plugin/plugin.json", '"version": "0.1.0"', '"version": "0.2.0"'), "version must be")

    def test_marketplace_version_name_and_source(self):
        self.assertRejects(lambda r: self.edit(r, ".github/plugin/marketplace.json", '"source": "./"', '"source": "./plugins/x"'), "source must be './'")
        self.assertRejects(lambda r: self.edit(r, ".github/plugin/marketplace.json", '"name": "mb-cohestra-agent-plugin"', '"name": "x"'), "name must be")
        self.assertRejects(lambda r: self.edit(r, ".github/plugin/marketplace.json", '"version": "0.1.0"\n  },', '"version": "0.2.0"\n  },'), "metadata.version")

    def test_invalid_json(self):
        self.assertRejects(lambda r: (r / "plugin.json").write_text("{ nope", encoding="utf-8"), "invalid JSON")

    def test_skill_name_mismatch(self):
        self.assertRejects(
            lambda r: self.edit(r, "skills/cohestra-engineering/SKILL.md", "name: cohestra-engineering", "name: other-skill"),
            "must equal the directory name",
        )

    def test_eval_case_without_a_grader(self):
        self.assertRejects(lambda r: shutil.rmtree(r / "evals/unrelated-request/graders"), "has no grader")

    def test_eval_case_with_only_an_llm_grader(self):
        def mutate(repo):
            graders = repo / "evals/delegates-security-review/graders"
            for path in graders.glob("*.md"):
                if path.name != "result.md":
                    path.unlink()
        self.assertRejects(mutate, "only on LLM graders")

    def test_eval_agent_match_with_an_unknown_agent(self):
        self.assertRejects(
            lambda r: self.edit(r, "evals/delegates-context-map/graders/coordinator-called.md", "mb-cohestra-coordinator", "cohestra-context-reader"),
            "unknown agent",
        )

    def test_eval_prompt_with_an_unknown_key(self):
        self.assertRejects(
            lambda r: self.edit(r, "evals/unrelated-request/prompt.md", "runs: 3", "runs: 3\nbogus: 1"),
            "unknown frontmatter key",
        )

    def test_missing_required_eval_case(self):
        self.assertRejects(lambda r: shutil.rmtree(r / "evals/writes-from-pattern"), "missing required eval case")

    def test_gitignore_without_the_results_entry(self):
        self.assertRejects(lambda r: self.edit(r, ".gitignore", "evals/results/\n", ""), ".gitignore must contain")

    def test_stale_product_name(self):
        self.assertRejects(lambda r: self.edit(r, "docs/PRODUCT.md", "Cohestra gives", "agent-review-suite gives"), "stale or placeholder")

    def test_placeholder_repository(self):
        self.assertRejects(lambda r: self.edit(r, "SUPPORT.md", "mbaic/mb-cohestra-agent-plugin", "OWNER/REPOSITORY"), "placeholder repository")

    def test_old_version_string(self):
        self.assertRejects(lambda r: self.edit(r, "docs/PRODUCT.md", "Cohestra gives", "Cohestra 4.0.0 gives"), "old version")

    def test_wrong_repository_name_in_a_url(self):
        self.assertRejects(lambda r: self.edit(r, "SUPPORT.md", "mbaic/mb-cohestra-agent-plugin", "mbaic/cohestra-agent-plugin"), "repository URL names")

    def test_missing_final_newline(self):
        def mutate(repo):
            path = repo / "SUPPORT.md"
            path.write_text(path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
        self.assertRejects(mutate, "missing final newline")

    def test_carriage_return(self):
        self.assertRejects(lambda r: self.edit(r, "SUPPORT.md", "# Support\n", "# Support\r\n"), "carriage return")

    def test_binary_file(self):
        self.assertRejects(lambda r: (r / "tool.bin").write_bytes(b"\x7fELF\x00\x01"), "binary file")

    def test_possible_secret(self):
        self.assertRejects(
            lambda r: self.edit(r, "SUPPORT.md", "# Support\n", "# Support\n\nkey: ghp_" + "a" * 36 + "\n"),
            "possible GitHub token",
        )

    def test_personal_machine_path(self):
        self.assertRejects(lambda r: self.edit(r, "SUPPORT.md", "# Support\n", "# Support\n\nSee /home/milos/code.\n"), "personal machine path")

    def test_banned_word_and_contraction(self):
        self.assertRejects(lambda r: self.edit(r, "docs/PRODUCT.md", "Cohestra gives", "Cohestra simply gives"), "avoid the word 'simply'")
        self.assertRejects(lambda r: self.edit(r, "docs/PRODUCT.md", "Cohestra gives", "Cohestra doesn't give"), "contraction")

    def test_worker_term(self):
        self.assertRejects(lambda r: self.edit(r, "docs/PRODUCT.md", "Cohestra gives", "Each worker gives"), "avoid the word 'worker'")

    def test_missing_required_file(self):
        self.assertRejects(lambda r: (r / "SUPPORT.md").unlink(), "missing required file: SUPPORT.md")

    def test_wrong_license(self):
        self.assertRejects(lambda r: self.edit(r, "LICENSE", "Milos Baic", "Someone Else"), "LICENSE")

    @unittest.skipUnless(HAS_YAML, "PyYAML is not installed")
    def test_release_workflow_must_be_manual(self):
        self.assertRejects(
            lambda r: self.edit(r, ".github/workflows/release.yml", "on:\n  workflow_dispatch:", "on:\n  push:\n  workflow_dispatch:"),
            "must run only on workflow_dispatch",
        )

    @unittest.skipUnless(HAS_YAML, "PyYAML is not installed")
    def test_eval_workflow_must_not_run_on_pull_requests(self):
        self.assertRejects(
            lambda r: self.edit(r, ".github/workflows/eval.yml", "on:\n  workflow_dispatch:", "on:\n  pull_request:\n  workflow_dispatch:"),
            "must run only on workflow_dispatch",
        )

    def test_eval_workflow_must_pin_models_and_gate_cost(self):
        self.assertRejects(lambda r: self.edit(r, ".github/workflows/eval.yml", "--max-cost-usd", "--cost"), "missing --max-cost-usd")

    def test_leftover_workflow_is_rejected(self):
        self.assertRejects(
            lambda r: (r / ".github/workflows/evals.yml").write_text("name: Old evals\non: workflow_dispatch\n", encoding="utf-8"),
            "unexpected workflow",
        )

    def test_long_sentence_gives_a_warning_and_not_an_error(self):
        long_text = "\n\nThis sentence " + "keeps going and going " * 8 + "until it ends.\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            with (repo / "docs/PRODUCT.md").open("a", encoding="utf-8") as handle:
                handle.write(long_text)
            report, _ = validate.run(repo)
        self.assertEqual(report.errors, [])
        self.assertTrue(any("sentence over" in w for w in report.warnings), report.warnings)

    def test_workflow_that_can_print_a_secret(self):
        self.assertRejects(
            lambda r: self.edit(r, ".github/workflows/validate.yml", "run: python scripts/validate.py", 'run: echo "${{ secrets.TOKEN }}"'),
            "can print a secret",
        )

    @unittest.skipUnless(HAS_YAML, "PyYAML is not installed")
    def test_invalid_yaml_file(self):
        self.assertRejects(lambda r: (r / ".github/ISSUE_TEMPLATE/bug_report.yml").write_text("a: [unclosed\n", encoding="utf-8"), "invalid YAML")

    def test_tab_in_yaml(self):
        self.assertRejects(lambda r: (r / ".github/ISSUE_TEMPLATE/bug_report.yml").write_text("a:\n\tb: 1\n", encoding="utf-8"), "tab character")

    def test_missing_pyyaml_warns_locally_and_fails_in_ci_mode(self):
        with mock.patch.object(validate, "yaml", None):
            local = self.run_mutated(lambda r: None)
            strict = self.run_mutated(lambda r: None, require_yaml=True)
        self.assertEqual(local.errors, [])
        self.assertTrue(any("PyYAML" in w for w in local.warnings))
        self.assertTrue(any("PyYAML" in e for e in strict.errors))

    def test_fixture_script_syntax_error(self):
        if not HAS_BASH:
            self.skipTest("bash is not available")
        self.assertRejects(lambda r: (r / "evals/improves-tests/fixture.sh").write_text("#!/usr/bin/env bash\nif then\n", encoding="utf-8"), "shell syntax error")

    def test_tracked_eval_results(self):
        if shutil.which("git") is None:
            self.skipTest("git is not available")

        def mutate(repo):
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "evals/results/run1").mkdir(parents=True)
            (repo / "evals/results/run1/report.html").write_text("<html></html>\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", "evals/results/run1/report.html"], cwd=repo, check=True)
        self.assertRejects(mutate, "tracked by Git")


class PackageTests(unittest.TestCase):
    def build(self, repo: Path, out: Path):
        return package.build_zip(repo, out, VERSION)

    def test_archive_layout_and_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            (repo / "evals/results/run1").mkdir(parents=True)
            (repo / "evals/results/run1/report.html").write_text("x\n", encoding="utf-8")
            (repo / "scripts/__pycache__").mkdir(exist_ok=True)
            (repo / "scripts/__pycache__/x.pyc").write_bytes(b"\x00")
            (repo / ".pytest_cache").mkdir()
            (repo / ".pytest_cache/v").write_text("x\n", encoding="utf-8")
            (repo / ".env").write_text("TOKEN=x\n", encoding="utf-8")
            (repo / "old.zip").write_bytes(b"PK")
            (repo / "notes.tmp").write_text("x\n", encoding="utf-8")
            (repo / ".git").mkdir()
            (repo / ".git/config").write_text("x\n", encoding="utf-8")
            archive, checksum, entries = self.build(repo, Path(tmp) / "out")
            self.assertEqual(archive.name, "mb-cohestra-agent-plugin-v0.1.0.zip")
            self.assertEqual(checksum.name, "mb-cohestra-agent-plugin-v0.1.0.zip.sha256")
            self.assertEqual(package.verify_zip(archive, entries), [])
            names = zipfile.ZipFile(archive).namelist()
            self.assertEqual({n.split("/", 1)[0] for n in names}, {"mb-cohestra-agent-plugin"})
            self.assertEqual(names, sorted(names))
            for forbidden in (".git/", "evals/results", "__pycache__", ".pytest_cache", ".env", "old.zip", "notes.tmp"):
                self.assertFalse(any(forbidden in n for n in names), forbidden)
            for required in (".claude-plugin/plugin.json", ".github/workflows/release.yml", ".github/plugin/marketplace.json",
                             "plugin.json", "agents/mb-cohestra-coordinator.md",
                             "com.github.copilot/agents/mb-cohestra-coordinator.agent.md",
                             "skills/cohestra-engineering/SKILL.md"):
                self.assertIn(f"mb-cohestra-agent-plugin/{required}", names)

    def test_archive_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            first, _, _ = self.build(repo, Path(tmp) / "one")
            second, _, _ = self.build(repo, Path(tmp) / "two")
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_checksum_file_format_and_value(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            archive, checksum, _ = self.build(repo, Path(tmp) / "out")
            digest, name = checksum.read_text(encoding="utf-8").split()
            self.assertEqual(name, archive.name)
            self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_scripts_are_executable_in_the_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            archive, _, _ = self.build(repo, Path(tmp) / "out")
            with zipfile.ZipFile(archive) as bundle:
                mode = bundle.getinfo("mb-cohestra-agent-plugin/evals/delegates-context-map/fixture.sh").external_attr >> 16
                self.assertEqual(mode & 0o777, 0o755)
                readme = bundle.getinfo("mb-cohestra-agent-plugin/README.md").external_attr >> 16
                self.assertEqual(readme & 0o777, 0o644)

    def test_main_builds_a_valid_archive_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = package.main(["--root", str(repo), "--output-dir", str(Path(tmp) / "dist")])
            self.assertEqual(code, 0, out.getvalue())
            self.assertIn("SHA-256:", out.getvalue())
            self.assertTrue((Path(tmp) / "dist/mb-cohestra-agent-plugin-v0.1.0.zip").is_file())

    def test_main_refuses_to_package_a_broken_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_repo(Path(tmp))
            path = repo / "com.github.copilot/agents/mb-cohestra-test-engineer.agent.md"
            path.write_text(path.read_text(encoding="utf-8").replace("user-invocable: false", "user-invocable: true", 1), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = package.main(["--root", str(repo), "--output-dir", str(Path(tmp) / "dist")])
            self.assertEqual(code, 1)
            self.assertFalse((Path(tmp) / "dist").exists())

    def test_release_notes_extraction(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        body = release_notes.extract("0.1.0", text)
        self.assertIn("First Cohestra product preview.", body)
        self.assertNotIn("releases/tag", body)
        self.assertNotIn("## [0.1.0]", body)
        self.assertIsNone(release_notes.extract("9.9.9", text))
        self.assertEqual(release_notes.extract("1.0.0", "## [1.0.0] - x\n\n## [0.9.0] - y\nold\n"), "")


if __name__ == "__main__":
    unittest.main()
