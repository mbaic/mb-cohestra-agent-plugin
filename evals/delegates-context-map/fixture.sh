#!/usr/bin/env bash
set -eu
mkdir -p src test docs
cat > src/login.js <<'EOT'
import { verify } from './token.js';
export function login(token) { return verify(token); }
EOT
cat > src/token.js <<'EOT'
export function verify(token) { return token === 'valid'; }
EOT
cat > test/login.test.js <<'EOT'
import { login } from '../src/login.js';
test('valid token', () => { expect(login('valid')).toBe(true); });
EOT
printf '%s\n' '# Notes' > docs/notes.md
