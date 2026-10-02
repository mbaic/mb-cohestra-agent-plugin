---
name: plans-architecture-without-edits
description: The agents plan a storage migration and edit nothing.
tags: [smoke, planning]
runs: 3
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the Cohestra Coordinator to plan the migration from local file storage to object storage. Do not edit files.
