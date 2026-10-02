---
name: updates-documentation
description: The agents document new configuration keys with correct defaults.
tags: [edit, documentation]
runs: 3
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the mb-Cohestra Coordinator to update the setup guide docs/setup.md for the new configuration keys in src/config.js. Check all examples.
