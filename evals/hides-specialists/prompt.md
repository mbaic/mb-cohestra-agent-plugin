---
name: hides-specialists
tags: [configuration]
runs: 1
max_turns: 4
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep]
plugins: ["../.."]
---
Read the plugin agent files. State which agent is user-selectable and whether specialist agents are hidden.
