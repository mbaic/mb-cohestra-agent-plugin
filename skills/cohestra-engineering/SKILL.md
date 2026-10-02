---
name: cohestra-engineering
description: Coordinates software engineering work with search-first discovery, bounded delegation to specialist agents, evidence checks, and one final result. Use for planning, implementation, diagnosis, testing, security and quality assessment, documentation, and code review.
---

# Cohestra engineering

Use this skill to coordinate software engineering work. The mb-Cohestra Coordinator agent follows the same rules. Clients that load only skills can apply them without the agents.

## Classify the task

Decide the task type before you act. One request can have several types.

- Planning: design a feature, migration, or refactor. Do not edit files.
- Implementation: make a focused change.
- Diagnosis: find the cause of a defect and correct it.
- Assessment: check correctness, security, quality, or compatibility.
- Testing: add or improve tests.
- Documentation: update the text that a change affects.

## Find repository instructions

1. Read `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `CONTRIBUTING.md` when they exist.
2. Read the build, lint, and test configuration.
3. Follow the rules that you find. They override these defaults.

## Search before you read

- Search for symbols, paths, and exact matches first.
- Read narrow line ranges. Do not read a whole large file without a reason.
- Skip generated files, vendored trees, lockfiles, binaries, and build output unless the task needs them.
- Stop when more reading is unlikely to change the result.

## Delegate within bounds

- Delegate only when a specialist adds value.
- Give each specialist one task, a file scope, constraints, and an output format.
- Give file pointers, not copied file contents, when the workspace is shared.
- Run tasks in parallel only when they do not overlap. Never let two specialists edit the same file at the same time.
- Keep architecture, security, concurrency, and ambiguous debugging decisions with the stronger roles.
- Use mechanical edits only after you identify a local reference pattern.

## Require evidence

- Check each material claim against a file or command output.
- Cite a file path and a line or symbol for each finding.
- Separate facts from assumptions.
- Do not report a test or command as passed unless it ran and returned success.

## Edit and run commands safely

- Make the smallest change that meets the requirement.
- Do not change files outside the scope.
- Ask the user before an action that can change public behavior, security, data handling, or that can delete data.
- Do not commit, push, merge, publish, or deploy unless the user asks and the client permits it.

## Test and document

- Add or update tests when behavior changes. Run the narrowest related tests first.
- Update documentation when user behavior, APIs, configuration, setup, or operations change.
- Check each documented command and example against the code.

## Final response

Use this structure when it applies. Omit empty sections.

```text
Result
Work completed
Files changed
Checks run
Risks
Open questions
```
