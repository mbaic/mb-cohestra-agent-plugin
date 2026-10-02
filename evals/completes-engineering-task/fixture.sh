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
cat > src/order.js <<'EOT'
export function createOrder(items) {
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return { items, total };
}
EOT
mkdir -p test
cat > test/order.test.js <<'EOT'
import test from 'node:test';
import assert from 'node:assert/strict';
import { createOrder } from '../src/order.js';

test('createOrder sums item totals', () => {
  assert.equal(createOrder([{ price: 2, quantity: 3 }]).total, 6);
});
EOT
mkdir -p docs
cat > docs/orders.md <<'EOT'
# Orders

`createOrder(items)` returns an order with the items and the total price.
EOT
