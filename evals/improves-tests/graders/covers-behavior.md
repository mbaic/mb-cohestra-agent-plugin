---
type: regex
pattern: '^(?=[\s\S]*timeout)(?=[\s\S]*(?:retry|attempts))'
flags: i
target: { source: file, path: test/retry-timeout.test.js }
---
