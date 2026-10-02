---
name: delegates-security-review
tags: [smoke, security, delegation]
runs: 3
max_turns: 10
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Agent]
plugins: ["../.."]
---
Review this code for concrete security defects:

`src/query.js`:
```js
export async function findUser(db, name) {
  return db.query(`SELECT * FROM users WHERE name = '${name}'`);
}
```
