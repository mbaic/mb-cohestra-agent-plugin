# Multi-Agent Review Coordinator

A coordinator-led plugin for focused repository review.

The plugin gives users one visible agent: **Coordinator**. Coordinator delegates narrow tasks to six hidden specialist agents and returns one report.

One Agent Plugins 1.0 package works with:

- VS Code Local sessions.
- VS Code Copilot sessions.
- GitHub Copilot CLI.
- GitHub Copilot app.

The package has no hooks and no MCP server.

## Agent team

| Agent | User can select | Coordinator can call | Role |
|---|---:|---:|---|
| Coordinator | Yes | No | Selects specialists, delegates work, merges findings, and returns one report |
| Context Reader | No | Yes | Maps relevant files, symbols, flows, tests, and commands |
| Architecture Reviewer | No | Yes | Reviews boundaries, dependencies, state, and data flow |
| Security Reviewer | No | Yes | Reviews concrete security defects and trust boundaries |
| Implementation Reviewer | No | Yes | Reviews correctness, failures, concurrency, and maintainability |
| Test Reviewer | No | Yes | Reviews coverage, assertions, isolation, and determinism |
| Pattern Writer | No | Yes | Makes small changes from verified local patterns |

Specialists cannot call other specialists. Coordinator is the only top-level delegation point.

## How it works

1. You select **Coordinator**.
2. You give a review request.
3. Coordinator finds the relevant scope.
4. Coordinator calls only the specialists that the task needs.
5. Each specialist works in a narrow context.
6. Coordinator removes duplicate findings.
7. Coordinator returns one prioritized report.

The agents search before they read. They use narrow file reads. These rules can reduce unnecessary context use. They do not guarantee a fixed token saving.

## Target support

| Target | Available | Main use |
|---|---:|---|
| VS Code Local session | Yes | Interactive work with editor and extension tools |
| VS Code Copilot session | Yes | Copilot-hosted coding sessions |
| GitHub Copilot CLI | Yes | Terminal-based repository work |
| GitHub Copilot app | Yes | Desktop agent sessions and parallel work |
| Copilot cloud agent | Agent profile compatible | Independent work that can return a pull request |

The agents do not set `target` or a fixed model. Each supported client selects its environment and an available model.

## Install in VS Code

1. Update VS Code.
2. Enable `chat.plugins.enabled`.
3. Open the Command Palette.
4. Run **Chat: Install Plugin From Source**.
5. Enter `https://github.com/OWNER/REPOSITORY`.
6. Review the source.
7. Confirm the installation.
8. Open Chat or the Agents window.
9. Select **Coordinator**.

For local development, clone the repository and add:

```json
{
  "chat.pluginLocations": {
    "/absolute/path/to/multi-agent-review-coordinator": true
  }
}
```

## Install in Copilot CLI

Install the plugin from its marketplace with the plugin commands in your installed Copilot CLI version. Start Copilot CLI. Select **Coordinator** from the agent list.

VS Code can also find plugins installed by Copilot CLI in `~/.copilot/installed-plugins/`.

## Use the plugin

Select **Coordinator**. Give it a narrow request.

```text
Review the authentication change for correctness and security.
```

```text
Review this pull request. Report only defects that can cause a failure.
```

```text
Map the payment flow. Then review its error handling and tests.
```

```text
Add one test that follows the existing test pattern. Run the narrow test command.
```

## Permissions

Review specialists can only read and search. Pattern Writer can edit files and execute commands when the client grants permission. Review each requested action before approval.

## Validate

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

Run one low-cost eval:

```bash
claude plugin eval . \
  --case delegates-context-map \
  --runs 1 \
  --ablation none \
  --scaffold \
  --no-publish
```

Run the full eval suite:

```bash
claude plugin eval . \
  --scaffold \
  --threshold 0.8 \
  --no-publish \
  --max-cost-usd 20
```

Claude Code evals use real model calls. They consume plan capacity or API funds.

## Publish

1. Replace `OWNER/REPOSITORY`.
2. Replace `Repository owner`.
3. Update the copyright owner.
4. Run validation and evals.
5. Create a release tag for version 4.0.0.

## Structure

```text
multi-agent-review-coordinator/
├── plugin.json
├── skills/
│   └── coordinated-repository-review/
│       └── SKILL.md
├── com.github.copilot/
│   └── agents/
│       ├── coordinator.agent.md
│       └── specialist agents
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── Claude Code mirrors
├── evals/
├── scripts/
├── tests/
└── .github/
```

## License

MIT
