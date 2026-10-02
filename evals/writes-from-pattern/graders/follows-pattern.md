---
type: regex
pattern: '^(?=[\s\S]*export function getInvoice\(id\))(?=[\s\S]*db\.find\(.invoices., id\))'
target: { source: file, path: src/handlers/get-invoice.js }
---
