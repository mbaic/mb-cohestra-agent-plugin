---
name: completes-engineering-task
description: The agents change code, add tests, and update documents in one task.
tags: [edit, coordination]
runs: 3
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit]
plugins: ["../.."]
---
Use the Cohestra Coordinator to make createOrder reject an item with a quantity that is not a positive integer. It must throw a RangeError. Add tests in test/order-quantity.test.js and update docs/orders.md. Follow the existing patterns. Do not run commands.
