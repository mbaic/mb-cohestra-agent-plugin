# Support

## Where to ask

- Open an [issue](https://github.com/mbaic/mb-cohestra-agent-plugin/issues/new/choose) for a defect that you can reproduce, or for a documentation problem.
- Use GitHub Discussions for usage questions, if the repository enables them.
- Do not report a vulnerability in a public issue. Follow [SECURITY.md](SECURITY.md).

## What to include

Give this information in each report:

1. The client and its version. Examples are VS Code, GitHub Copilot CLI, the GitHub Copilot app, and Claude Code.
2. The Cohestra version from `plugin.json`.
3. The operating system.
4. The prompt that you sent to mb-Cohestra Coordinator.
5. Steps to reproduce the problem.
6. Logs with secrets and private code removed.

## Before you open an issue

1. Update the client and the plugin.
2. Read the troubleshooting table in the [README](README.md#troubleshooting).
3. Run `python3 scripts/validate.py` in a clone, when the problem is in the package files.
