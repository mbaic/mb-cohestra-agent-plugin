# Cohestra

**Coordinated software engineering.**

Cohestra coordinates specialist AI agents for software engineering work. You use one visible agent: **mb-Cohestra Coordinator**.

The coordinator defines the task. It selects the required specialists. It checks their work. It returns one result.

> Cohestra can plan, build, test, secure, document, and assess software. Code review is one capability. It is not the product boundary.

A *plugin* is a package that adds agents and skills to an AI client. A *specialist* is a hidden agent with one engineering role. An *eval* is a test that sends a prompt to a real model and grades the result.

## Agents

The package has one visible agent and eight specialists.

| Agent | ID | Visible | Purpose |
|---|---|:-:|---|
| mb-Cohestra Coordinator | `mb-cohestra-coordinator` | Yes | Defines the result, plans delegation, checks outputs, and reports one result. |
| mb-Cohestra Context Analyst | `mb-cohestra-context-analyst` | No | Finds relevant files, symbols, dependencies, tests, and repository rules. |
| mb-Cohestra Software Architect | `mb-cohestra-software-architect` | No | Designs boundaries, interfaces, data flow, migration steps, and failure isolation. |
| mb-Cohestra Implementation Engineer | `mb-cohestra-implementation-engineer` | No | Makes focused code and configuration changes. |
| mb-Cohestra Security Engineer | `mb-cohestra-security-engineer` | No | Assesses trust boundaries, access control, input, secrets, dependencies, and sensitive data. |
| mb-Cohestra Test Engineer | `mb-cohestra-test-engineer` | No | Designs, writes, and runs focused tests. |
| mb-Cohestra Quality Engineer | `mb-cohestra-quality-engineer` | No | Checks correctness, compatibility, maintenance, performance, and regression risk. |
| mb-Cohestra Documentation Engineer | `mb-cohestra-documentation-engineer` | No | Updates affected user, operator, API, and developer documentation. |
| mb-Cohestra Pattern Writer | `mb-cohestra-pattern-writer` | No | Produces mechanical files and repetitive edits from a verified local pattern. |

The Copilot agent picker shows only mb-Cohestra Coordinator. The coordinator can call only these eight specialists. A specialist cannot call another agent.

## How it works

1. You select **mb-Cohestra Coordinator**.
2. You describe the task.
3. The coordinator restates the result and the constraints.
4. The coordinator searches the repository before it reads files.
5. The coordinator gives bounded tasks to the specialists that add value.
6. Each specialist works in a narrow scope and returns evidence.
7. The coordinator checks the claims against files and command output.
8. The coordinator returns one result.

The agents search before they read. They read narrow file ranges. They pass file paths, not copied files. These rules can reduce context use. They do not guarantee a fixed token saving.

## Capabilities

Cohestra can do these tasks:

- Explore a repository.
- Plan a feature, migration, or refactor.
- Design interfaces and component boundaries.
- Implement a focused change.
- Diagnose and correct a defect.
- Add and run tests.
- Assess security and quality risks.
- Update affected documentation.
- Review code and current changes.
- Coordinate several roles for one result.

## Boundaries

- Cohestra uses only the tools that the active client provides.
- Actions follow the permission and sandbox rules of the client.
- Cohestra does not commit, push, merge, publish, or deploy unless you request the action and the client permits it.
- The plugin is not read-only. Some specialists have edit and execute tools.
- The package contains no hooks, MCP server, background service, or telemetry code.
- Source code enters the model context when an agent reads it. Check the data policy of your organization before you use Cohestra on private code.
- AI output can be wrong. Review each change before you release it.

The package adds no telemetry code. The host client has its own data practices. Read its documentation.

## Package

```text
mb-cohestra-agent-plugin/
├── plugin.json                       Agent Plugins 1.0 manifest
├── skills/cohestra-engineering/      Portable skill
├── com.github.copilot/agents/        Copilot agents (source of truth)
├── .claude-plugin/plugin.json        Claude Code manifest
├── agents/                           Claude Code mirrors (generated)
├── .github/                          Marketplace, workflows, templates
├── evals/                            Claude Code behavioral evals
├── scripts/                          Sync, validate, and package scripts
├── tests/                            Unit tests
└── docs/                             Product, architecture, development, testing
```

## Install

Each client keeps its own copy of the plugin. Install and update it in each client that you use.

### VS Code

1. Enable the `chat.plugins.enabled` setting.
2. Open the Command Palette.
3. Run **Chat: Install Plugin From Source**.
4. Enter `https://github.com/mbaic/mb-cohestra-agent-plugin`.
5. Review the source and confirm the installation.
6. Open Copilot Chat.
7. Select **mb-Cohestra Coordinator**.

### VS Code local development

Clone the repository. Register the clone in your VS Code settings:

```json
{
  "chat.pluginLocations": {
    "/absolute/path/to/mb-cohestra-agent-plugin": true
  }
}
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add mbaic/mb-cohestra-agent-plugin
copilot plugin install cohestra@mb-cohestra-agent-plugin
```

Start Copilot CLI. Select **mb-Cohestra Coordinator** from the agent list.

### GitHub Copilot app

The app documentation describes this path. See [Customize the GitHub Copilot app](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app).

1. Click **Customize** in the sidebar. Then click **Plugins**.
2. Click the settings icon next to the marketplace dropdown.
3. Add the GitHub repository `mbaic/mb-cohestra-agent-plugin` and follow the prompts.
4. Find **cohestra** in the list. Click **Install**.

The documentation lists no command for this install. Agent support depends on the tools that the app provides.

### Claude Code

The Claude Code files are a compatibility layer. This repository does not publish a Claude Code marketplace. Load the plugin from a local clone:

```bash
git clone https://github.com/mbaic/mb-cohestra-agent-plugin
claude --plugin-dir ./mb-cohestra-agent-plugin
```

To start a session as the coordinator, add `--agent cohestra:mb-cohestra-coordinator`.

## Use

Select **mb-Cohestra Coordinator**. Give it a task and the constraints. The examples below use Business Central AL development. They assume that an AL app is open in your workspace.

Build a feature:

```text
Add a Customer Rating field to the Customer table with a table extension. Show it on the Customer Card with a page extension. Use the object ID range from app.json and the name prefix of the other objects. Add an AL test and update the documentation.
```

Plan a change:

```text
Plan the move of this extension from Business Central on-premises to SaaS. List the AL code that SaaS does not allow, such as DotNet variables and file system access. Do not edit files.
```

Correct a defect:

```text
Find the cause of the failing test codeunit for posting a sales invoice. The error says that the posting date is not within the range of allowed posting dates. Make the smallest safe correction. Run the related tests.
```

Review current changes:

```text
Check the current changes for correctness, performance, permissions, and missing tests. Look for missing SetLoadFields calls, FindSet calls inside loops, hard-coded text, and objects that have no permission set entry. Do not edit files.
```

Add tests:

```text
Add AL tests for the credit limit check on the sales order. Use the Library - Sales and Library Assert codeunits. Cover a customer under the limit, over the limit, and blocked. Do not change production code.
```

Update documentation:

```text
Update the README for the new setup page. List each field, its default value, and the permission set that grants access. Check each field name against the page object.
```

### More prompts

Use these as starting points. Replace the object names, the fields, and the versions with your own.

Explore an app:

```text
Map how a sales order moves from release to posting in this app. List the codeunits, the event subscribers, and the tables that we extend. Do not edit files.
```

Design an extensible interface:

```text
Design an interface and an extensible enum for payment export formats, so that a partner can add a format without changing our code. List the migration steps in order. Do not edit files.
```

Check permissions:

```text
Check the permission sets in this app. Find objects that have no permission entry, and find codeunits that run with elevated permissions. Do not edit files.
```

Check performance:

```text
Check the item ledger report for slow reads. Look for missing SetLoadFields calls, missing keys, and FlowField calculations inside loops. Do not edit files.
```

Add a small feature:

```text
Add a Send Reminder action to the Customer Ledger Entries page. Follow the pattern of the existing actions. Add one test.
```

Refactor safely:

```text
Move the duplicated posting date checks in our sales codeunits into one helper codeunit. Keep the behavior the same. Run the related tests.
```

Plan an upgrade:

```text
Plan the upgrade of this app from Business Central 24 to 25. List the breaking changes that affect our objects, the obsolete elements that we use, and the steps for the upgrade codeunit. Do not edit files.
```

Copy a pattern:

```text
Add the table extension and the page extensions for a Vendor Rating field on the Vendor Card and the Vendor List. Copy the pattern of the Customer Rating extensions.
```

Check the build setup:

```text
Check the AL-Go for GitHub settings files in this repository. List the settings that affect the build, the test run, and the app folders. Do not edit files.
```

Combine roles:

```text
Fix the failing posting test. Add a regression test. Update the release notes in the changelog.
```

### Tips for good prompts

- State whether Cohestra can edit files. Write "Do not edit files" for a plan or a review.
- Name the app, the object type, and the object ID or range when you know them.
- Say whether the target is SaaS or on-premises, and give the Business Central version.
- Ask for the checks that you want, such as "Run the related tests". Cohestra runs only the commands that your client allows.
- Describe one result. The coordinator splits the work.
- Cohestra reads AL source as text. It does not replace the AL compiler. Build the app in VS Code to confirm a change.
- In Claude Code, start with "Use the mb-Cohestra Coordinator to". Claude Code has no agent picker.

## Client support

| Client | Supported | Agent source | Notes |
|---|:-:|---|---|
| VS Code Copilot Chat | Yes | `com.github.copilot/agents/` | Needs `chat.plugins.enabled`. |
| VS Code Local and Copilot sessions | Yes | `com.github.copilot/agents/` | The agent files set no `target` field. |
| GitHub Copilot CLI | Yes | `com.github.copilot/agents/` | Installs from the marketplace file in `.github/plugin/`. |
| GitHub Copilot app | Yes | `com.github.copilot/agents/` | Subject to the tools that the app provides. |
| Claude Code | Compatibility layer | `agents/`, `.claude-plugin/` | Loads from a local clone. |

Runtime behavior depends on the active client, the session type, the repository policy, and the granted tools. Clients do not expose identical tools or permissions.

The Agent Plugins 1.0 manifest in `plugin.json` takes precedence in Copilot clients. The visibility fields in the Copilot agent files do not control the Claude Code interface. The one-visible-agent rule applies to the supported Copilot pickers.

## Validate

Run these commands from the repository root. They need Python 3.10 or later and make no network calls.

```bash
python3 scripts/sync_claude_agents.py --check
python3 scripts/validate.py
python3 tests/run.py
```

The validator checks manifests, agent visibility, the delegation allowlist, Claude mirrors, the skill, eval cases, workflows, forbidden components, stale names, and file endings. Add `--online` to compare the manifest with the live Agent Plugins schema. Install PyYAML and add `--require-yaml` to check YAML files with a full parser.

Claude Code can also check the plugin files:

```bash
claude plugin validate . --strict
```

## Evaluate

Evals test behavior with real model calls. They count against your plan usage or your API bill. They need Claude Code 2.1.269 or later, and Git 2.31 or later when Git is installed. Set a cost ceiling.

Run the read-only smoke cases once. This command needs no extra tool grant:

```bash
claude plugin eval . --scaffold --tag smoke --runs 1 --ablation none --no-publish
```

Run the full suite. The edit cases need the `Write` and `Edit` tools:

```bash
claude plugin eval . --scaffold --allow-tools Write Edit --threshold 0.8 --no-publish --max-cost-usd 20
```

Claude Code has no agent picker, so each Cohestra prompt starts with "Use the mb-Cohestra Coordinator to". The edit cases need a spawn depth of 2 or more. See [docs/TESTING.md](docs/TESTING.md).

The `--scaffold` flag runs each fixture script as you, outside the agent sandbox. Use it only for suites that you trust.

## Update

| Client | Update |
|---|---|
| VS Code | Install the plugin from source again. For a local plugin, run `git pull` in the clone. |
| GitHub Copilot CLI | `copilot plugin update cohestra` |
| GitHub Copilot app | Open **Customize** and **Plugins**. Reinstall the plugin. |
| Claude Code | Run `git pull` in the clone. Start a new session. |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No Cohestra agent in VS Code | Plugins are off. The default is off. | Enable `chat.plugins.enabled`. |
| The coordinator does not call specialists in VS Code | An older VS Code version gates custom subagents, or the `agent` tool is off. | Update VS Code. In VS Code 1.109, enable `chat.customAgentInSubagent.enabled`. |
| In Claude Code, the coordinator cannot call specialists | The spawn depth is below 2. The call fails with `Task is disabled for this session`. | Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to 2 or more. The default is 3. |
| The picker shows more than one Cohestra agent | The client reads the Claude Code mirrors. Documentation says the clients do not. | Update the client. Open an issue with the client name and version. |
| A Cohestra agent does not run | A project agent with the same name replaces the plugin agent. | Rename the project agent. |
| Marketplace not found in Copilot CLI | The marketplace is not registered. | Run `copilot plugin marketplace list`. Add it again. |
| Changes have no effect | The client holds an old copy. | Update or reinstall the plugin. |
| `sync_claude_agents.py --check` fails | A mirror is stale. | Run `python3 scripts/sync_claude_agents.py`. |
| An eval case reports a tool as `not granted` | The case needs `Write` or `Edit`. | Add `--allow-tools Write Edit`. |
| An eval run stops at a trust prompt | The plugin directory is not trusted. | Run once in a terminal. In CI, pass `--trust-plugin`. |
| A baseline run reports `Agent type ... not found` | The no-plugin arm cannot call plugin agents. | This is expected. Use `--ablation none` to skip it. |

## Security

Read the agent files before you install a plugin. mb-Cohestra Coordinator delegates edit and execute actions to specialists. The client asks you to approve each action that its rules protect.

The package has no hooks, MCP server, background service, or telemetry code. Report a vulnerability through a private GitHub security advisory. Do not open a public issue. See [SECURITY.md](SECURITY.md).

## Contributing

Edit agents in `com.github.copilot/agents/`. Run the sync script. Run the validator and the tests. Write in short, direct sentences. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

MIT. See [LICENSE](LICENSE).
