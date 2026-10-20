# Review context

Synthetic, complete working-tree snapshot. Review without edits. All invoice inputs
are validated. An empty invoice list is valid. This snapshot is not runnable;
test results below are author-supplied evidence, not reviewer-executed checks.

## Current request and available authority

The user asks for the first invoice's label, or `null` for an empty list, plus a
filter returning only unpaid invoices in their original order without mutating the
input. Lists have at most 100 rows. There is no external library or official BP
document needed to establish these behaviors.

There is no documented repository rule about filter versus reduce, helper
extraction, or callback naming. Two other feature modules use reduce for their own
independently owned calculations; neither implements invoice filtering.

## Past advice and current decision

`review-notes/old-comment.md` records a previous reviewer's one-time suggestion:
"Maybe use reduce for list operations so the code looks consistent."
It was not adopted as policy. A memory note summarizes that suggestion; it is not a
new user instruction or an additional repository rule.

For this review the user explicitly says: "Keep the small local filtering function;
do not introduce an abstraction just to match the other feature's style. Still
report behavior defects."

## Patch

```diff
diff --git a/src/invoices/firstInvoiceLabel.ts b/src/invoices/firstInvoiceLabel.ts
--- a/src/invoices/firstInvoiceLabel.ts
+++ b/src/invoices/firstInvoiceLabel.ts
@@ -1,5 +1,4 @@
 type Invoice = { label: string; paid: boolean };
 export function firstInvoiceLabel(rows: readonly Invoice[]): string | null {
-  if (rows.length === 0) return null;
   return rows[0].label;
 }
diff --git a/src/invoices/unpaidInvoices.ts b/src/invoices/unpaidInvoices.ts
new file mode 100644
--- /dev/null
+++ b/src/invoices/unpaidInvoices.ts
@@ -0,0 +1,4 @@
+type Invoice = { label: string; paid: boolean };
+export function unpaidInvoices(rows: readonly Invoice[]): readonly Invoice[] {
+  return rows.filter((row) => !row.paid);
+}
```

## Caller and available checks

The unchanged `src/invoices/previewLabel.ts` calls
`firstInvoiceLabel(rows) ?? "No invoices"`, including when `rows` is empty. No
caller guard prevents that input, and no error handler supplies the empty label.

Existing filter tests cover empty, all-paid and mixed lists, order preservation
and input immutability; the author reports they passed. There is no test for the
empty input in `firstInvoiceLabel`. There are no other changed files, callers or
shared implementations of these invoice operations.
