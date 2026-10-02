# Migration from version 3

| Version 3 | Version 4 |
|---|---|
| Plugin: `agent-review-suite` | Plugin: `multi-agent-review-coordinator` |
| Agent: `orchestrator` | Agent: `coordinator` |
| Display name: Review Orchestrator | Display name: Coordinator |
| Skill: `lean-repository-review` | Skill: `coordinated-repository-review` |

Uninstall version 3 before you install version 4. The new plugin uses a different package name and agent ID. Remove any local configuration that refers to `agent-review-suite` or `orchestrator`.
