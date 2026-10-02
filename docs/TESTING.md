# Testing

Cohestra has three test layers. Static validation and unit tests need no credentials. Behavioral evals need Claude Code credentials and cost money.

## Static validation

```bash
python3 scripts/sync_claude_agents.py --check
python3 scripts/validate.py
```

The validator fails on:

- Invalid JSON, YAML, or frontmatter.
- A root manifest that breaks the closed Agent Plugins schema.
- A manifest name other than `cohestra`, or a version other than `0.1.0`.
- A marketplace name or source mismatch.
- A missing agent file.
- More or fewer than one visible Copilot agent, or a visible name other than `mb-Cohestra Coordinator`.
- A specialist that is visible, blocked from the coordinator, or able to delegate.
- A coordinator allowlist outside the roster.
- A `target` or `model` field in an agent file.
- A hooks directory, a hook file, `mcp.json`, or `.mcp.json`.
- A Claude mirror that differs from its Copilot source.
- A skill name that differs from its directory.
- An eval case without a grader, or with only LLM graders.
- Tracked `evals/results/` content, or a missing `.gitignore` entry.
- Stale product names, placeholder values, and possible secrets.
- A missing final newline, a carriage return, or a binary file.

The validator warns, and does not fail, when the live schema check is unavailable. Run `python3 scripts/validate.py --online` to compare the manifest with the live schema. The local structural check always runs.

Claude Code can run its own file check:

```bash
claude plugin validate . --strict
```

## Unit tests

```bash
python3 tests/run.py
```

The tests need no credentials and make no model call. They cover product identity, manifest keys, agent names, visibility, the allowlist, hidden specialist behavior, mirror sync, the skill, eval structure, `.gitignore`, stale names, README sections, and final newlines.

The tests also check the validator itself. Each case copies the repository, adds one defect, and checks that the validator rejects it. Examples are a visible specialist, a `target` field, a hooks directory, and a stale mirror.

One test builds each eval fixture and applies the deterministic graders. A grader must reject the untouched fixture and accept a correct result.

## Claude plugin evals

An *eval* sends a prompt to a real model with the plugin loaded. Graders then check the final message, the tool calls, and the files.

Requirements:

- Claude Code 2.1.269 or later.
- Git 2.31 or later, when Git is installed.
- Valid Claude Code credentials.
- Real model calls. They count against plan usage or API billing.
- A cost ceiling in CI.

### Cases

| Case | Tags | Needs | Result graders | Process graders |
|---|---|---|---|---|
| `delegates-context-map` | smoke | read | Names the three login files | Calls the coordinator |
| `plans-architecture-without-edits` | smoke | read | Plan names the storage module, an interface, and rollback. An LLM judges the plan | Calls the coordinator. Makes no `Write` or `Edit` call |
| `implements-focused-change` | edit | `Write`, `Edit` | New function and test files exist. The function is exported. The test imports it | Calls the coordinator and a specialist |
| `delegates-security-review` | smoke | read | Names SQL injection and a parameterized fix. An LLM judges the answer | Calls the coordinator |
| `improves-tests` | edit | `Write`, `Edit` | New test file covers timeout and retry. The production file is unchanged | Calls the coordinator, then the Test Engineer or the Implementation Engineer |
| `updates-documentation` | edit | `Write`, `Edit` | Setup guide lists both keys with the correct defaults. The code is unchanged | Calls the coordinator and the Documentation Engineer |
| `writes-from-pattern` | edit | `Write`, `Edit` | New handler follows the local pattern | Calls the coordinator and the Pattern Writer |
| `completes-engineering-task` | edit | `Write`, `Edit` | Code, test, and document all change | Calls the coordinator and a specialist. At least two Cohestra calls |
| `reviews-without-edits` | smoke | read | Names injection and the missing authorization check. An LLM judges the review | Calls the coordinator. Makes no `Write` or `Edit` call |
| `unrelated-request` | smoke | none | Answers `4` | Makes no Agent call |

Each case has a prompt, run limits, only the tools that it needs, and at least one deterministic grader. The cases that need repository state use a `fixture.sh` scaffold script. No case needs the `Bash` tool.

### How the cases select the coordinator

Claude Code has no agent picker. A Claude Code user selects the coordinator by name. Each Cohestra prompt therefore starts with "Use the mb-Cohestra Coordinator to". The negative case, `unrelated-request`, does not name it.

This matters. Without the name, the main model often does a small task itself and calls no Cohestra agent. A run on a three-file fixture showed this: the model read the files and answered correctly, and no Cohestra agent ran.

### What the traces show

A maintainer checked real traces with Claude Code 2.1.287:

- The plugin loads. The session lists nine agents as `cohestra:<agent-id>` and the skill as `cohestra:cohestra-engineering`.
- A delegation is a tool call named `Agent`. Its input has a `subagent_type` field with the namespaced ID, for example `cohestra:mb-cohestra-coordinator`.
- A call that the coordinator makes appears in the same trace. It has a `parent_tool_use_id` field that points to the coordinator call.
- The coordinator has no edit tool. In the edit cases a correct run delegates the edit to a specialist. The `specialist-called` grader checks this.

The `input_match` value is a regular expression. It matches the namespaced ID as text. It does not name the `subagent_type` field, so a change in the trace layout does not break it.

### Nesting depth

The edit cases run the main thread, then the coordinator, then a specialist. This needs a spawn depth of 2 or more. Claude Code allows 3 by default. The `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` environment variable changes the limit, and `eval.yml` sets it to 3.

A sandbox that sets the value to 1 blocks the specialist call. The nested call fails with `Task is disabled for this session, in subagents as well as here`. The main session then makes the edit itself, and the `specialist-called` grader fails. Set the variable to 3 for the run:

```bash
CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=3 claude plugin eval . --scaffold --allow-tools Write Edit --no-publish
```

### Grader choices

- `regex` checks required text or file content. Edit cases grade file contents, because `file_exists` sees only files that the run created.
- `file_exists` checks created files.
- `tool_used` checks agent calls and the absence of edit tools.
- `llm` gives a short semantic judgment on a few cases. No case relies on it alone.

### Inspect a real trace

Run one case. Keep its temporary directory. Write the result to a JSON file:

```bash
claude plugin eval . --case implements-focused-change --runs 1 --ablation none --scaffold \
  --allow-tools Write Edit --no-publish --keep-temp --json results.json
```

The result holds a `tracePath` for each run, in `cases[].arms.with[]`. The trace is a JSON Lines file. Each line is one message. Read the `tool_use` blocks to see each Agent call.

The kept directory can hold files that the agent wrote. Remove it when you finish: `chmod -R u+rwX <dir> && rm -rf <dir>`.

### Local fast eval

Run the read-only smoke cases once. This needs no tool grant.

```bash
claude plugin eval . --scaffold --tag smoke --runs 1 --ablation none --no-publish
```

### Full run

The edit cases need the `Write` and `Edit` tools.

```bash
claude plugin eval . --scaffold --allow-tools Write Edit --threshold 0.8 --no-publish --max-cost-usd 20
```

The `--scaffold` flag runs each `fixture.sh` as you, outside the agent sandbox. Use it only on a suite that you trust. Never run it on an untrusted pull request.

### Baseline comparison

By default Claude Code runs each case twice: with the plugin and without it. The score difference shows what the plugin adds.

```bash
claude plugin eval . --scaffold --allow-tools Write Edit --ablation with-without --threshold 0.8 --no-publish --max-cost-usd 40
```

In the without-plugin runs, a call to a Cohestra agent fails with `Agent type ... not found`. This is expected. The delta never changes the exit code.

### Cost and credentials

Each run is a real model call. The `--max-cost-usd` ceiling is a list-price estimate. It does not cap plan usage. Runs that already started can pass the ceiling. When the ceiling stops the suite, the command exits with code 2 and writes partial results.

Eval output goes to `evals/results/`. Git ignores this directory. The package script excludes it.

## CI behavior

| Workflow | Trigger | Needs | Purpose |
|---|---|---|---|
| `validate.yml` | Push and pull request | Nothing | Sync check, validator, unit tests, shell syntax, and a package build |
| `eval.yml` | Manual | `ANTHROPIC_API_KEY` secret | Paid evals with pinned models, a threshold, and a cost ceiling |
| `release.yml` | Manual | Nothing | Checks, build, tag, release, and checksum upload |

`eval.yml` never runs on a pull request. A fork cannot read the secret, and a fixture script runs as the runner user.

The eval job fails when the secret is missing. It pins the agent model and the judge model. It passes `--trust-plugin`, `--scaffold`, `--json`, and `--no-publish`. It archives the JSON result and the HTML report. The job fails on the exit code of the eval command.

## Reporting results

Report the two categories separately.

```text
Static checks: passed or failed
Behavioral evals: passed, failed, or not run
```

Do not state that evals passed unless they ran with valid credentials and finished.
