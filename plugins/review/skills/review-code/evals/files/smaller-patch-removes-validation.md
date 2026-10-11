# Review context

Review this working-tree refactor, report only. Request: simplify batch preview
construction while preserving its contract. `parseBatchSize` accepts a form value
that converts to an integer from 1 through 100; every other value must be rejected
before constructing the preview. No change to these limits was approved.

The sole consumer, unchanged `src/batches/previewBatch.ts`, is:

```ts
import { parseBatchSize } from "./parseBatchSize";

export function previewBatch(raw: unknown): string[] {
  const size = parseBatchSize(raw);
  return Array.from({ length: size }, (_, index) => `Item ${index + 1}`);
}
```

The UI passes the raw form string to `previewBatch`, catches parser errors to
show an invalid-size message, and otherwise renders the returned list. No other
validation is applied to this input. The existing module is the only owner of
the batch-size policy; there is no installed schema library or alternate parser.

## Patch

```diff
diff --git a/src/batches/parseBatchSize.ts b/src/batches/parseBatchSize.ts
--- a/src/batches/parseBatchSize.ts
+++ b/src/batches/parseBatchSize.ts
@@ -1,7 +1,4 @@
 export function parseBatchSize(raw: unknown): number {
-  const size = Number(raw);
-  if (!Number.isInteger(size) || size < 1 || size > 100) {
-    throw new Error("Invalid batch size");
-  }
-  return size;
+  // shortcut: the form normally sends valid sizes; revisit for other clients.
+  return Number(raw);
 }
```

## Verification evidence

The supplied existing tests assert `"1"` and `"100"` produce those sizes, and
`"0"`, `"-1"`, `"13.5"`, `"101"`, and `"oops"` throw `Invalid batch size`.
Those tests were not changed. There is no supplied execution result for this
patch. This snapshot is not a runnable checkout; do not claim commands ran.

There are no other changed, staged, unstaged, or untracked files.
