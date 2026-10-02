# Contributing

Thank you for helping with Cohestra. Keep each change small and focused.

## Setup

1. Install Python 3.10 or later and Git.
2. Optional: install PyYAML (`python3 -m pip install pyyaml`). The validator then checks YAML files with a full parser.
3. Clone the repository.
4. Create a branch.

The scripts need no other package and make no network calls.

## Authoritative files

| What | Where | Rule |
|---|---|---|
| Agent prompts | `com.github.copilot/agents/*.agent.md` | Edit these files. They are the source of truth. |
| Claude Code mirrors | `agents/*.md` | Do not edit. Run the sync script. |
| Portable skill | `skills/cohestra-engineering/SKILL.md` | Edit by hand. |
| Product constants | `scripts/cohestra_common.py` | Update with the roster, tools, and version. |
| Manifests | `plugin.json`, `.claude-plugin/plugin.json`, `.github/plugin/marketplace.json` | Keep name and version equal. |

## Change an agent

1. Edit the file in `com.github.copilot/agents/`.
2. Run `python3 scripts/sync_claude_agents.py`.
3. Run the validation commands below.
4. Add or update an eval case when behavior changes.
5. Update `CHANGELOG.md` for each user-visible change.

Do not add hooks, an MCP server, a background service, or telemetry. Do not show a specialist in the user picker. Do not add a `target` or `model` field to an agent file.

## Validate

```bash
python3 scripts/sync_claude_agents.py --check
python3 scripts/validate.py
python3 tests/run.py
```

## Evaluate

Evals use real model calls and count against plan usage or API billing. Run them when you change a prompt.

```bash
claude plugin eval . --scaffold --tag smoke --runs 1 --ablation none --no-publish
claude plugin eval . --scaffold --allow-tools Write Edit --threshold 0.8 --no-publish --max-cost-usd 20
```

See [docs/TESTING.md](docs/TESTING.md).

## Writing rules

Write in ASD-STE100 Simplified Technical English where practical.

- Use short sentences. Give one instruction in each sentence.
- Use active voice and direct instructions.
- Use one term for one concept. Use `specialist`, not `worker`.
- Avoid contractions, idioms, humor, and sales claims.
- Avoid the words `simply`, `obviously`, and `just`.
- Use **Cohestra Coordinator** as the full name of the visible agent.

The validator checks the banned words and contractions in Markdown files.

## Pull requests

- Describe the change and the reason for it.
- Complete the checklist in the pull request template.
- State the eval result, or write "not run" and the reason.
- Do not include secrets, tokens, private URLs, or personal paths.

## Security

Do not report a vulnerability in a public issue. Use a [private security advisory](https://github.com/mbaic/mb-cohestra-agent-plugin/security/advisories/new). See [SECURITY.md](SECURITY.md).
