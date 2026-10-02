# Architecture

## Control model

Coordinator is the only user-selectable agent. It can call an explicit allowlist of six specialists. Each specialist has `agents: []` and cannot delegate work.

## Visibility model

Coordinator uses:

```yaml
user-invocable: true
disable-model-invocation: true
```

The user can select Coordinator. Other agents cannot select it as a subagent.

Each specialist uses:

```yaml
user-invocable: false
disable-model-invocation: false
agents: []
```

The user cannot select a specialist. Coordinator can call it. It cannot call another specialist.

## Context model

- Search before file reads.
- Use targeted ranges.
- Delegate narrow questions.
- Keep specialist handbacks short.
- Merge duplicate findings at the coordinator.
- Keep only evidence-based findings.

Prompt rules guide this behavior. They cannot enforce a token limit or guarantee a fixed saving.
