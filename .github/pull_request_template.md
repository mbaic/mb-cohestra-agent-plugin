## Summary

Describe the change and the reason for it.

## Type of change

- [ ] Agent prompt or tool change
- [ ] Skill change
- [ ] Script, test, or workflow change
- [ ] Documentation change
- [ ] Eval case change

## Checks

- [ ] I edited agents in `com.github.copilot/agents/` and ran `python3 scripts/sync_claude_agents.py`.
- [ ] `python3 scripts/sync_claude_agents.py --check` passes.
- [ ] `python3 scripts/validate.py` passes.
- [ ] `python3 tests/run.py` passes.
- [ ] I updated `CHANGELOG.md` for each user-visible change.
- [ ] I ran the evals, or I state below why I did not.
- [ ] The change adds no hooks, MCP server, background service, telemetry, or install script.
- [ ] The change contains no secrets, tokens, private URLs, or personal paths.

## Eval status

State the eval command that you ran and the result. Write "not run" and the reason when you did not run evals.
