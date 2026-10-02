# Development

This document explains how to change Cohestra and keep the package consistent.

## Authoritative files

| File or directory | Role |
|---|---|
| `com.github.copilot/agents/*.agent.md` | Source of truth for agent prompts and visibility. |
| `agents/*.md` | Generated Claude Code mirrors. Never edit by hand. |
| `skills/cohestra-engineering/SKILL.md` | Portable skill. Edit by hand. |
| `scripts/cohestra_common.py` | Product constants: name, version, roster, tool policy. |
| `plugin.json` | Agent Plugins 1.0 manifest. |
| `.claude-plugin/plugin.json` | Claude Code manifest. |
| `.github/plugin/marketplace.json` | Copilot CLI marketplace. The repository is its own marketplace. |
| `evals/` | Claude Code behavioral eval cases. |

## Frontmatter convention

Write each frontmatter key on one line. Use flow lists such as `tools: [read, search]`. Quote a value that contains a colon, a hash, or a comma inside a list item.

The validator parses this subset with a built-in parser. When PyYAML is installed, the validator also parses the frontmatter with PyYAML and fails when the two results differ. This catches a valid YAML file that a client could read in a different way.

## Sync the Claude mirrors

```bash
python3 scripts/sync_claude_agents.py          # write the mirrors
python3 scripts/sync_claude_agents.py --check  # exit 1 when a mirror is stale
```

The output is deterministic. The script needs no network access.

## Add or change an agent

1. Edit or create the file in `com.github.copilot/agents/`. Use the suffix `.agent.md`.
2. For a new specialist, add it to `SPECIALISTS` and `TOOL_POLICY` in `scripts/cohestra_common.py`.
3. For a new specialist, add its display name to the `agents` list of the coordinator. Add it to the specialist list in the coordinator prompt.
4. Keep the specialist contract and the handback form in each specialist prompt. The validator checks both.
5. Run the sync script.
6. Add or update an eval case. See [TESTING.md](TESTING.md).
7. Update the README agent table and `docs/ARCHITECTURE.md`.
8. Run the validation commands.

Do not set `target` or `model` in an agent file. Do not give a specialist the `agent` tool.

## Update the version

The version appears in these places. Change all of them in one commit.

1. `PLUGIN_VERSION` in `scripts/cohestra_common.py`
2. `plugin.json`
3. `.claude-plugin/plugin.json`
4. `.github/plugin/marketplace.json`, in `metadata.version`
5. `.github/plugin/marketplace.json`, in the plugin entry
6. `CHANGELOG.md`, as a new section
7. The default input of `.github/workflows/release.yml`

The validator fails when a manifest disagrees with `PLUGIN_VERSION`. The release workflow fails when its input disagrees with the manifests.

## Validate and package

```bash
python3 scripts/sync_claude_agents.py --check
python3 scripts/validate.py
python3 tests/run.py
python3 scripts/package.py
```

The package script runs the validator first. It writes `dist/cohestra-agent-plugin-v<version>.zip` and a `.sha256` file. The archive has one top-level `cohestra-agent-plugin/` directory. It excludes `.git/`, `evals/results/`, caches, temporary files, existing ZIP files, and environment files.

## Avoid drift

- Run the sync script after each agent edit.
- Keep the version in all places equal. The validator checks it.
- Update the README, the architecture document, and the tests with each roster change.
- Run the eval smoke cases after each prompt change.
- Use the same term for the same idea. Use `specialist`, not `worker`.

## Script safety

The validation and packaging scripts read repository files and write local output. They start no background process. They make no network call by default. The `--online` flag of `scripts/validate.py` fetches the public Agent Plugins schema and nothing else. The package itself contains no network client code.
