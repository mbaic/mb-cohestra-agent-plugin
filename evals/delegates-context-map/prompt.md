---
name: delegates-context-map
description: The agents map the files that control a login flow.
tags: [smoke, delegation]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Agent]
plugins: ["../.."]
---
Use the Cohestra Coordinator to map the files that control login and its tests. Return only paths, symbols, and a short flow. Do not propose changes.
