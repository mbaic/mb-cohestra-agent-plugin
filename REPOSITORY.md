# Repository settings

This file holds values that the repository owner can copy into GitHub settings. The release checklist and the branch protection items are recommendations, not facts about the current settings.

## Values

```text
Repository name: mb-cohestra-agent-plugin
Description: Cohestra coordinates specialist AI agents for software engineering in VS Code, GitHub Copilot CLI, and the GitHub Copilot app.
Homepage: https://github.com/mbaic/mb-cohestra-agent-plugin
Topics: agent-plugins, github-copilot, copilot-cli, vscode, software-engineering, multi-agent, software-quality, ai-agents
```

Use the repository URL as the homepage until a product site exists.

## Product values

| Item | Value |
|---|---|
| Product name | Cohestra |
| Plugin ID | `cohestra` |
| Version | `0.1.0` |
| Visible agent | mb-Cohestra Coordinator (`mb-cohestra-coordinator`) |
| Tagline | Coordinated software engineering. |
| Short message | One coordinator. Specialist agents. One engineering result. |
| License | MIT |
| Release archive | `mb-cohestra-agent-plugin-v0.1.0.zip` |

## Secrets

| Secret | Used by | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | `.github/workflows/eval.yml` | Only to run the paid evals |

The validate and release workflows need no secret. They use the built-in `GITHUB_TOKEN`.

## Release checklist (recommendation)

1. Choose the new version. Use the form `0.2.0`, with no leading `v`.
2. Update the version in `scripts/cohestra_common.py`, `plugin.json`, `.claude-plugin/plugin.json`, and `.github/plugin/marketplace.json` (two places).
3. Add a section for the version to `CHANGELOG.md`. Use the release date.
4. Run `python3 scripts/sync_claude_agents.py --check`, `python3 scripts/validate.py`, and `python3 tests/run.py`.
5. Run the evals when you changed a prompt. Record the result in the pull request.
6. Merge the pull request after the validate workflow passes.
7. Open **Actions**, select **Release**, and run the workflow with the version.
8. Check the release assets: the ZIP and the `.sha256` file.
9. Run `sha256sum -c` on the downloaded files.

A tag is not an install boundary. Clients install from the default branch unless you configure a ref.

## Branch protection (recommendation)

Protect the default branch with these rules:

- Require a pull request before merge.
- Require the status checks from the **Validate** workflow.
- Require branches to be up to date before merge.
- Block force pushes and branch deletion.
- Require conversation resolution before merge.

Also protect tags that match `v*`. Set the default workflow token permission to read-only.

## Optional settings (recommendation)

- Enable private vulnerability reporting. The security policy links to it.
- Enable GitHub Discussions if you want a place for usage questions.
- Add an `evals` environment with required reviewers. Reference it from the eval workflow when you want an approval step before paid runs.
