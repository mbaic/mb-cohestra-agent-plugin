---
name: writes-from-pattern
description: The agents create one more handler from a local pattern.
tags: [edit, pattern]
runs: 3
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the Cohestra Coordinator to add src/handlers/get-invoice.js. Follow the existing handler pattern exactly. The table name is invoices.
