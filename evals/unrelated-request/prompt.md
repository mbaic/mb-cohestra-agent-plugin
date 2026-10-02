---
name: unrelated-request
description: A trivial question must not trigger delegation.
tags: [smoke, negative]
runs: 3
max_turns: 4
timeout_seconds: 120
allowed_tools: [Agent]
plugins: ["../.."]
---
What is 2 plus 2? Answer with only the number.
