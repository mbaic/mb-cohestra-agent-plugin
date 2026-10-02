# Architecture

Cohestra is an Agent Plugins 1.0 package. It has one visible coordinator, eight hidden specialists, and one portable skill. It has no hooks and no MCP server.

## Control model

mb-Cohestra Coordinator is the only agent that a user can select. It delegates bounded tasks to specialists. Each specialist returns a short handback. The coordinator checks the handbacks and returns one result.

```text
User ──> mb-Cohestra Coordinator ──> Specialist (one bounded task) ──> handback
              │                                                       │
              └─────────────── checks evidence, returns one result <──┘
```

## Agent names

Every agent ID starts with `mb-cohestra-`. Every display name starts with `mb-Cohestra`. The plugin ID stays `cohestra`.

Copilot clients have no namespace for agents. They match an agent by its `name` field, and the coordinator allowlist lists display names. Two plugins that ship an agent with the same name can clash. A project agent with the same name as a plugin agent silently replaces the plugin agent. The `mb-` prefix makes a clash unlikely and groups these agents in a picker.

Claude Code adds the plugin name to each agent. The full name is `cohestra:mb-cohestra-coordinator`.

## Visibility model

The Copilot agent files are the source of truth. They use two frontmatter fields to control visibility.

The coordinator:

```yaml
user-invocable: true
disable-model-invocation: true
```

The user can select the coordinator. Other agents cannot call it as a subagent.

Each specialist:

```yaml
user-invocable: false
disable-model-invocation: false
agents: []
```

The user cannot select a specialist. The coordinator can call it. The specialist cannot call another agent.

## Delegation allowlist

The coordinator sets an explicit `agents` list with the display names of the eight specialists. The `agent` tool in its `tools` list enables delegation.

VS Code documents that an agent listed in `agents` can be called even when it sets `disable-model-invocation: true`. Cohestra does not rely on that rule for specialists. Specialists set `disable-model-invocation: false`.

No specialist has the `agent` tool. Each specialist also sets `agents: []`. This blocks nested delegation. The validator fails when a specialist has the `agent` tool or a non-empty list.

## Tool policy

Each agent has the minimum tools for its role.

| Agent | Copilot tools | Claude Code tools |
|---|---|---|
| mb-Cohestra Coordinator | `read`, `search`, `agent` | Read, Glob, Grep, Agent |
| mb-Cohestra Context Analyst | `read`, `search` | Read, Glob, Grep |
| mb-Cohestra Software Architect | `read`, `search` | Read, Glob, Grep |
| mb-Cohestra Implementation Engineer | `read`, `search`, `edit`, `execute` | Read, Glob, Grep, Edit, Write, Bash |
| mb-Cohestra Security Engineer | `read`, `search`, `execute` | Read, Glob, Grep, Bash |
| mb-Cohestra Test Engineer | `read`, `search`, `edit`, `execute` | Read, Glob, Grep, Edit, Write, Bash |
| mb-Cohestra Quality Engineer | `read`, `search`, `execute` | Read, Glob, Grep, Bash |
| mb-Cohestra Documentation Engineer | `read`, `search`, `edit` | Read, Glob, Grep, Edit, Write |
| mb-Cohestra Pattern Writer | `read`, `search`, `edit` | Read, Glob, Grep, Edit, Write |

The coordinator has no edit or execute tool. It delegates both. This keeps its context small and keeps the roles separate.

The Security Engineer has `execute` for read-only checks, such as a dependency audit that the repository already supports. Its prompt forbids commands that change files, install packages, or send repository data out.

## Copilot source files and Claude mirrors

Edit the Copilot files in `com.github.copilot/agents/`. The script `scripts/sync_claude_agents.py` generates the Claude Code mirrors in `agents/`.

The sync script:

- Converts the file name from `.agent.md` to `.md`.
- Maps the tool aliases to Claude Code tool names.
- Keeps `name`, `description`, and `tools`. It drops the Copilot-only fields.
- Keeps the prompt body byte-identical.
- Fails on an unknown field or tool alias. It never drops content in silence.

The Claude mirrors set no `model` field. They inherit the model of the session. The evals pin models through the workflow flags `--model` and `--judge-model`, not through the agent files.

## Portable skill

`skills/cohestra-engineering/SKILL.md` carries the shared rules: task classification, instruction discovery, search-first reads, delegation bounds, evidence, safe edits, tests, documentation, and the final response structure. The skill name equals its directory name. A client that loads only skills can apply the rules without the agents.

## Context efficiency

The agents use prompt rules to keep context small:

- Search before you read.
- Read narrow ranges. Prefer symbols, paths, and exact matches.
- Skip generated files, vendored trees, lockfiles, binaries, and build output.
- Ask the Context Analyst for one compact map before several specialists inspect the same area.
- Pass file pointers, not copied contents, when the workspace is shared.
- Limit each handback to decisions, evidence, changed paths, checks, and open items.
- Use the Pattern Writer only after the coordinator finds a local reference pattern.
- Use the stronger roles for ambiguity, architecture, security, concurrency, and debugging.

The first version of this design drew on a Spotify engineering article about routing bulk file reading to cheaper models: [Portal by Spotify](https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90). The article reports about 90 percent mean savings on bulk reading in four test scenarios. It does not report a saving for all token use. Cohestra applies the routing ideas as prompt rules only. It uses no hooks and no cheaper-model routing, and it claims no fixed saving.

## No hooks and no MCP server

The package contains no hooks, no MCP server, no background service, and no telemetry code. The validator fails on a hooks directory, a hook file, `mcp.json`, `.mcp.json`, and the matching manifest keys. It also fails on a binary file or an install script.

## Client behavior

These points come from the client documentation that the maintainers checked.

| Client | Behavior |
|---|---|
| VS Code | A root `plugin.json` that declares the Agent Plugins `$schema` uses Agent Plugins semantics. VS Code reads Copilot components from the `com.github.copilot` directory and ignores other namespaces. |
| GitHub Copilot CLI | A root `plugin.json` that declares the Agent Plugins `$schema` takes precedence over `.claude-plugin/plugin.json`. For this format the CLI reads agents from `com.github.copilot/agents/`, not from the root `agents/` directory. It reads the marketplace file from `.github/plugin/marketplace.json`. |
| GitHub Copilot app | Installs plugins from the **Plugins** view under **Customize**. It reads Agent Plugins packages. |
| Claude Code | Reads `.claude-plugin/plugin.json` and `agents/`. It dispatches plugin agents as `cohestra:<agent-id>`. |

## Known limits

- **Picker visibility.** The visibility fields apply to the Copilot pickers. They do not control the Claude Code interface. The one-visible-agent rule applies to supported Copilot pickers only.
- **Claude Code allowlist.** The Claude mirror of the coordinator lists the `Agent` tool without a type list. Claude Code applies a type list only when an agent runs as the main thread, and this package does not set one. Specialists have no `Agent` tool, so they cannot delegate.
- **Claude Code nesting depth.** In Claude Code, the main thread calls the coordinator, and the coordinator calls a specialist. This needs a spawn depth of 2 or more. Claude Code allows 3 by default. When the limit is 1, the nested call fails with `Task is disabled for this session, in subagents as well as here`. The coordinator then cannot delegate. Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to 2 or more.
- **Copilot CLI agent directories.** The CLI documents the `agents/` directory for legacy plugins only. This package declares Agent Plugins 1.0, so the CLI ignores the Claude Code mirrors in `agents/`. A project-level agent with the same name as a plugin agent silently replaces the plugin agent.
- **Subagent settings.** VS Code 1.109 gated custom agents as subagents behind the `chat.customAgentInSubagent.enabled` setting. Current VS Code documentation describes custom subagents as available by default. Older versions can still need the setting.
- **Tools differ by client.** A client can grant fewer tools than an agent file requests. The agents state blocked checks in their handbacks.

## Trust and permission boundaries

- The client enforces permissions, sandbox rules, and tool approval. Cohestra does not change them.
- Cohestra never commits, pushes, merges, publishes, or deploys unless the user asks and the client permits it.
- Source code enters model context when an agent reads it. The user owns the data policy decision.
- The package adds no telemetry code. The host client has its own data practices.
