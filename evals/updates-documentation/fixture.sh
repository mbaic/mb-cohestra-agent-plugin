#!/usr/bin/env bash
set -eu
mkdir -p src
cat > src/config.js <<'EOT'
// cohestra-fixture: do not change.
export const config = {
  port: Number(process.env.PORT ?? 3000),
  rateLimitMax: Number(process.env.RATE_LIMIT_MAX ?? 100),
  rateLimitWindowSeconds: Number(process.env.RATE_LIMIT_WINDOW_SECONDS ?? 60),
};
EOT
mkdir -p docs
cat > docs/setup.md <<'EOT'
# Setup

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| PORT | 3000 | HTTP port |

## Start

Run `node src/server.js`.
EOT
