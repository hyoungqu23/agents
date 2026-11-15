# PR context

Title: Support archived invoices from billing API

Body: Archived invoices should be accepted and shown with an "Archived" status label. Existing issued and paid states must keep working.

Relevant patch:

```diff
diff --git a/src/api/invoiceSchema.ts b/src/api/invoiceSchema.ts
--- a/src/api/invoiceSchema.ts
+++ b/src/api/invoiceSchema.ts
@@ -4,4 +4,4 @@ import { z } from "zod";
 export const invoiceSchema = z.object({
   id: z.string(),
-  status: z.enum(["issued", "paid"]),
+  status: z.enum(["issued", "paid", "archived"]),
 });
diff --git a/src/api/toInvoice.ts b/src/api/toInvoice.ts
--- a/src/api/toInvoice.ts
+++ b/src/api/toInvoice.ts
@@ -6,6 +6,6 @@ import type { InvoiceDto } from "./invoiceSchema";
 export function toInvoice(dto: InvoiceDto): Invoice {
   return {
     id: dto.id,
-    status: dto.status,
+    status: dto.status as InvoiceStatus,
   };
 }
```

Relevant unchanged consumers:

```tsx
// src/domain/invoice.ts
export type InvoiceStatus = "issued" | "paid";

// src/invoices/InvoiceStatusLabel.tsx
const labels: Record<InvoiceStatus, string> = {
  issued: "Issued",
  paid: "Paid",
};

export function InvoiceStatusLabel({ status }: { status: InvoiceStatus }) {
  return <span>{labels[status]}</span>;
}
```

Assume no tests or other changed files exist. The fixture is not a runnable checkout.
