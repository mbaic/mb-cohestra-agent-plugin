#!/usr/bin/env bash
set -eu
cat > package.json <<'EOT'
{
  "name": "fixture",
  "private": true,
  "type": "module"
}
EOT
mkdir -p src
cat > src/retry.js <<'EOT'
// cohestra-fixture: production file. Do not change.
export async function withRetry(fn, { attempts = 3, timeoutMs = 1000 } = {}) {
  let lastError;
  for (let index = 0; index < attempts; index += 1) {
    try {
      return await Promise.race([
        fn(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), timeoutMs)),
      ]);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}
EOT
mkdir -p test
cat > test/retry.test.js <<'EOT'
import test from 'node:test';
import assert from 'node:assert/strict';
import { withRetry } from '../src/retry.js';

test('returns the first successful result', async () => {
  assert.equal(await withRetry(async () => 'ok'), 'ok');
});
EOT
