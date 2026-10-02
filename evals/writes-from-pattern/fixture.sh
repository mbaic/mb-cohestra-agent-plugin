#!/usr/bin/env bash
set -eu
mkdir -p src
cat > src/db.js <<'EOT'
export const db = {
  find(table, id) {
    return { table, id };
  },
};
EOT
mkdir -p src/handlers
cat > src/handlers/get-user.js <<'EOT'
import { db } from '../db.js';

export function getUser(id) {
  return db.find('users', id);
}
EOT
mkdir -p src/handlers
cat > src/handlers/get-order.js <<'EOT'
import { db } from '../db.js';

export function getOrder(id) {
  return db.find('orders', id);
}
EOT
mkdir -p src/handlers
cat > src/handlers/get-product.js <<'EOT'
import { db } from '../db.js';

export function getProduct(id) {
  return db.find('products', id);
}
EOT
