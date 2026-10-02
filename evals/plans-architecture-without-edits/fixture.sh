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
cat > src/storage.js <<'EOT'
import { mkdir, readFile, writeFile } from 'node:fs/promises';

const ROOT = './data';

export async function saveFile(name, bytes) {
  await mkdir(ROOT, { recursive: true });
  await writeFile(`${ROOT}/${name}`, bytes);
}

export async function readStoredFile(name) {
  return readFile(`${ROOT}/${name}`);
}
EOT
mkdir -p src
cat > src/upload.js <<'EOT'
import { saveFile } from './storage.js';

export async function upload(request) {
  await saveFile(request.name, request.bytes);
  return { status: 201 };
}
EOT
mkdir -p src
cat > src/download.js <<'EOT'
import { readStoredFile } from './storage.js';

export async function download(request) {
  return { status: 200, body: await readStoredFile(request.name) };
}
EOT
