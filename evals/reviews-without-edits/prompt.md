---
name: reviews-without-edits
description: The agents review a patch and edit nothing.
tags: [smoke, review]
runs: 3
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the mb-Cohestra Coordinator to check the change in changes.patch for correctness, security, compatibility, and missing tests. Do not edit files.
