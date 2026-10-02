#!/usr/bin/env bash
set -eu
cat > changes.patch <<'EOT'
--- a/src/users.js
+++ b/src/users.js
@@ -1,3 +1,8 @@
 export function listUsers(db, page, pageSize) {
-  return db.query('SELECT id, name FROM users LIMIT ? OFFSET ?', [pageSize, page * pageSize]);
+  const offset = page * pageSize;
+  return db.query(`SELECT id, name, email FROM users LIMIT ${pageSize} OFFSET ${offset}`);
 }
+
+export function deleteUser(db, requester, id) {
+  return db.query('DELETE FROM users WHERE id = ' + id);
+}
EOT
