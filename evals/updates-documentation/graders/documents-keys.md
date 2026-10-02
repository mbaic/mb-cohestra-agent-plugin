---
type: regex
pattern: '^(?=[\s\S]*RATE_LIMIT_MAX[^\n]*100)(?=[\s\S]*RATE_LIMIT_WINDOW_SECONDS[^\n]*60)'
target: { source: file, path: docs/setup.md }
---
