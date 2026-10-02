---
name: delegates-security-review
description: The agents find a SQL injection defect in a snippet.
tags: [smoke, security, delegation]
runs: 3
max_turns: 10
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Agent]
plugins: ["../.."]
---
Use the Cohestra Coordinator to review this code for concrete security defects:

`src/query.js`:
```js
export async function findUser(db, name) {
  return db.query(`SELECT * FROM users WHERE name = '${name}'`);
}
```
