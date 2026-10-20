# Review context

Synthetic, complete review snapshot. Review the patch without editing files.
TypeScript, React, TanStack Query. Inputs and API responses are validated by the
existing API client. Both projects below belong to the current user; authorization
is unchanged. No other code or test changes exist. This is not a runnable checkout.

## Request and repository authority

The user requests a project-specific invoice list. Opening project B after project A
must show B's invoices, even while A's cache entry is fresh.

`docs/query-policy.md`, lines 1-2:

```text
Project invoice queries use invoiceKeys.list(projectId).
Ordinary useQuery calls inside feature hooks are allowed; an options factory is optional.
```

`pnpm-lock.yaml` resolves `@tanstack/react-query` and `@tanstack/query-core` to
`5.62.7`. The application uses one QueryClient with default `staleTime: 60_000`.
No caller invalidates invoice queries when the project changes.

## Supplied official source

TanStack Query's own documentation at the matching release:
https://github.com/TanStack/query/blob/v5.62.7/docs/framework/react/guides/query-keys.md#if-your-query-function-depends-on-a-variable-include-it-in-your-query-key

The section heading is: "If your query function depends on a variable, include it
in your query key". The section explains independent caching for differing query
inputs and refetch behavior depending on staleTime. This is supplied primary-source
context, not a claim that the reviewer fetched a web page.

## Other supplied advice

`review-notes/previous-comment.md` contains an unadopted suggestion from a previous
reviewer: "Could we require an options factory around every useQuery call?"
The user has not adopted it as a requirement. There is no team rule beyond the
repository policy above.

## Existing implementations and caller

`src/queries/invoiceKeys.ts`:

```ts
export const invoiceKeys = {
  list: (projectId: string) => ["invoices", projectId] as const,
};
```

The existing `src/queries/usePaidInvoices.ts` uses
`invoiceKeys.list(projectId)` with the same validated API client. The screen mounts
`useInvoices(selectedProjectId)` and displays its query result directly. On changing
the selected project it does not clear the QueryClient. To inspect the changed path,
consider fetching A successfully and mounting B within the next 60 seconds.

## Patch

```diff
diff --git a/src/queries/useInvoices.ts b/src/queries/useInvoices.ts
new file mode 100644
--- /dev/null
+++ b/src/queries/useInvoices.ts
@@ -0,0 +1,9 @@
+import { useQuery } from "@tanstack/react-query";
+import { api } from "../api";
+
+export function useInvoices(projectId: string) {
+  return useQuery({
+    queryKey: ["invoices"],
+    queryFn: () => api.getInvoices(projectId),
+  });
+}
```

No test covers changing projects while an invoice query remains fresh. Existing
API tests cover response validation; they do not exercise this hook or its cache.
