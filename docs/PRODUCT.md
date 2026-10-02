# Product

**Coordinated software engineering.** One coordinator. Specialist agents. One engineering result.

## User problem

An engineering task needs several roles: exploration, design, implementation, testing, security checks, and documentation. A single AI session does all of them in one long context. The context grows, the roles blur, and the result is hard to check.

## Product promise

Cohestra gives you one entry point for a task. The coordinator splits the task into bounded parts. Specialists do the parts in narrow scopes. The coordinator checks the evidence and returns one result.

Cohestra does not promise a faster result or a lower cost. Prompt rules guide the behavior. They do not enforce a limit.

## Primary user

A software engineer or architect who works on a real repository with VS Code, GitHub Copilot CLI, the GitHub Copilot app, or Claude Code. The user reviews the result before release.

## Product terms

| Term | Meaning |
|---|---|
| Plugin | A package that adds agents and skills to an AI client. |
| Coordinator | The one visible agent. It defines the result and delegates work. Its full name is mb-Cohestra Coordinator. |
| Specialist | A hidden agent with one engineering role. It does bounded work and cannot delegate. |
| Delegation brief | The task, scope, constraints, and output format that the coordinator gives to a specialist. |
| Handback | The short report that a specialist returns to the coordinator. |
| Skill | A portable set of instructions that a client loads when a task needs it. |
| Eval | A test that sends a prompt to a real model and grades the result. |

## Capabilities

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

Code review is one capability. It is not the product boundary.

## Non-goals

- Cohestra is not a review-only tool.
- Cohestra does not replace human review.
- Cohestra does not commit, push, merge, publish, or deploy on its own.
- Cohestra ships no hooks, MCP server, background service, or telemetry code.
- Cohestra does not lock a model. The user or the session selects it.
- Cohestra does not promise a fixed token saving.
- Cohestra does not control the permissions of the host client.

## Safety boundaries

- The coordinator has read and search tools only. It delegates every edit and command.
- Each specialist has the minimum tools for its role.
- The coordinator asks the user before a decision that can change public behavior, security, data handling, or that can delete data.
- Specialists state uncertainty and blocked checks. They do not claim a passed test that did not run.
- The client enforces permissions and sandbox rules.

## Success criteria

The product meets its goal when these statements are true:

1. The Copilot agent picker shows only mb-Cohestra Coordinator from this plugin.
2. The coordinator can call only the eight specialists. A specialist cannot call an agent.
3. Static validation and the unit tests pass without credentials.
4. The behavioral evals meet their threshold when a maintainer runs them with valid credentials.
5. A user can install the plugin in each supported client with the steps in the README.
6. Each result lists the checks that ran and the checks that were blocked.
