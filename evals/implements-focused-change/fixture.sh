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
cat > src/text.js <<'EOT'
export function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
EOT
mkdir -p test
cat > test/text.test.js <<'EOT'
import test from 'node:test';
import assert from 'node:assert/strict';
import { capitalize } from '../src/text.js';

test('capitalize upper-cases the first character', () => {
  assert.equal(capitalize('abc'), 'Abc');
});
EOT
