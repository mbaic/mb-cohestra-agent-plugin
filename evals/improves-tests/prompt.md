---
name: improves-tests
description: The agents add timeout and retry tests and keep production code unchanged.
tags: [edit, testing]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the mb-Cohestra Coordinator to add tests for the timeout and retry behavior of withRetry. Put them in test/retry-timeout.test.js. Do not change production behavior. Do not run commands.
