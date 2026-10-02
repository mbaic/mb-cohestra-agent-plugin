---
type: llm
---
PASS if the response is an ordered migration plan that names the storage module, proposes an interface or adapter boundary, covers moving existing data and rollback, and does not claim that it changed any file.
FAIL if it has no ordered steps, ignores rollback, or says that it edited files.
