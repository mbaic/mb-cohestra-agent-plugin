# Contributing

1. Create a branch.
2. Make a focused change.
3. Edit Copilot agents in `com.github.copilot/agents/`.
4. Run `python3 scripts/sync_claude_agents.py`.
5. Run `python3 scripts/validate.py`.
6. Run `python3 -m unittest discover -s tests`.
7. Run evals when Claude Code credentials are available.
8. Open a pull request.

Use direct and short sentences. Do not add hooks. Do not expose specialist agents in the user picker.
