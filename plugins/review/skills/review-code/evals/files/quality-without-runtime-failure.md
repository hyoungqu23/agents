# Review context

Review the supplied working-tree change. Intent: show an invoice total, include that
same total in an export row, and add a fixed 30-second retry delay. No calculation
policy changes are intended. All amounts are validated safe nonnegative integers
and rates are validated upstream; authorization and transport validation are
unchanged. This snapshot contains every changed file and all relevant callers.
It is not a runnable checkout. Report findings without editing files.

Stack: TypeScript, React with Vite, Vitest. Repository scripts are `vitest run`,
`tsc --noEmit`, and `eslint .`; none can be executed against this snapshot.

## Repository authority: docs/architecture.md

- Invoice calculations are owned by `src/invoices/`; UI and export code use its
  public functions. Workers must not import modules from `src/ui/`.
- Duration names include their units. `sleep` accepts milliseconds.

## Existing code (unchanged)

`src/invoices/total.ts`:

```ts
export type InvoiceLine = { netCents: number; taxRate: number };

export function calculateInvoiceTotalCents(lines: readonly InvoiceLine[]): number {
  return lines.reduce((sum, line) => sum + Math.round(line.netCents * (1 + line.taxRate)), 0);
}
```

`src/checkout/invoiceAmount.ts`:

```ts
import { calculateInvoiceTotalCents, type InvoiceLine } from "../invoices/total";

export function invoiceAmount(lines: readonly InvoiceLine[]): number {
  return calculateInvoiceTotalCents(lines);
}
```

`src/retry/sleep.ts`:

```ts
export function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}
```

## Patch

```diff
diff --git a/src/ui/InvoiceSummary.tsx b/src/ui/InvoiceSummary.tsx
new file mode 100644
--- /dev/null
+++ b/src/ui/InvoiceSummary.tsx
@@ -0,0 +1,9 @@
+import type { InvoiceLine } from "../invoices/total";
+
+export function calculateTotalCents(lines: readonly InvoiceLine[]): number {
+  return lines.reduce((sum, line) => sum + Math.round(line.netCents * (1 + line.taxRate)), 0);
+}
+
+export function InvoiceSummary({ lines }: { lines: readonly InvoiceLine[] }) {
+  return <output>{calculateTotalCents(lines)} cents</output>;
+}
diff --git a/src/workers/toInvoiceRow.ts b/src/workers/toInvoiceRow.ts
new file mode 100644
--- /dev/null
+++ b/src/workers/toInvoiceRow.ts
@@ -0,0 +1,6 @@
+import type { InvoiceLine } from "../invoices/total";
+import { calculateTotalCents } from "../ui/InvoiceSummary";
+
+export function toInvoiceRow(lines: readonly InvoiceLine[]) {
+  return { totalCents: calculateTotalCents(lines) };
+}
diff --git a/src/retry/delay.ts b/src/retry/delay.ts
new file mode 100644
--- /dev/null
+++ b/src/retry/delay.ts
@@ -0,0 +1,5 @@
+const RETRY_DELAY_MS = 30_000;
+
+export function getRetryDelaySeconds(): number {
+  return RETRY_DELAY_MS;
+}
diff --git a/src/retry/waitBeforeRetry.ts b/src/retry/waitBeforeRetry.ts
new file mode 100644
--- /dev/null
+++ b/src/retry/waitBeforeRetry.ts
@@ -0,0 +1,6 @@
+import { getRetryDelaySeconds } from "./delay";
+import { sleep } from "./sleep";
+
+export async function waitBeforeRetry(): Promise<void> {
+  await sleep(getRetryDelaySeconds());
+}
```

## Available verification evidence

Existing invoice tests independently assert totals of 120 cents for one 100-cent
line at 20% tax, 121 cents for one 101-cent line at 20%, and zero for no lines.
The supplied UI and export checks cover these same cases. A fake-clock check
asserts that `waitBeforeRetry` finishes at 30,000 milliseconds. These checks pass
in the author's supplied CI summary; this reviewer has not run them.

There are no other staged, unstaged, untracked, generated, or changed files.
