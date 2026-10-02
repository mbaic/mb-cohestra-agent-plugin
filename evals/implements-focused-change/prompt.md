---
name: implements-focused-change
description: The agents add a function and its tests without a command tool.
tags: [edit, implementation]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the mb-Cohestra Coordinator to add a slugify function in src/slugify.js. It lowercases the text, replaces each run of non-alphanumeric characters with one hyphen, and removes hyphens at both ends. Follow the style of src/text.js. Add tests in test/slugify.test.js. Do not run commands.
