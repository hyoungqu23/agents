# Review context

Review this working-tree change without editing. The request adds two independent
policies: trial eligibility for the acquisition team and refund eligibility for
the billing team. Each currently uses a 14-day window; they are independently
approved and released, with no requirement that their windows stay equal.
Both policies must accept elapsed days from 0 through 13 and reject all other
values. Inputs are validated finite integer day counts at the existing service boundary.

Repository authority (`docs/domains.md`): domain policy belongs to the named
domain; there is no shared eligibility policy or shared duration configuration.
The complete symbol search for eligibility/day-window helpers finds only the two
added functions below. Language: TypeScript. Test runner: Vitest.

## Patch

```diff
diff --git a/src/acquisition/isTrialEligible.ts b/src/acquisition/isTrialEligible.ts
new file mode 100644
--- /dev/null
+++ b/src/acquisition/isTrialEligible.ts
@@ -0,0 +1,3 @@
+export function isTrialEligible(daysSinceSignup: number): boolean {
+  return daysSinceSignup >= 0 && daysSinceSignup < 14;
+}
diff --git a/src/billing/isRefundEligible.ts b/src/billing/isRefundEligible.ts
new file mode 100644
--- /dev/null
+++ b/src/billing/isRefundEligible.ts
@@ -0,0 +1,3 @@
+export function isRefundEligible(daysSincePurchase: number): boolean {
+  return daysSincePurchase >= 0 && daysSincePurchase < 14;
+}
diff --git a/src/eligibility.test.ts b/src/eligibility.test.ts
new file mode 100644
--- /dev/null
+++ b/src/eligibility.test.ts
@@ -0,0 +1,12 @@
+import { expect, it } from "vitest";
+import { isTrialEligible } from "./acquisition/isTrialEligible";
+import { isRefundEligible } from "./billing/isRefundEligible";
+
+it.each([-1, 0, 13, 14, 15])("checks the trial policy at day %i", (days) => {
+  expect(isTrialEligible(days)).toBe([0, 13].includes(days));
+});
+
+it.each([-1, 0, 13, 14, 15])("checks the refund policy at day %i", (days) => {
+  expect(isRefundEligible(days)).toBe([0, 13].includes(days));
+});
+
```

The supplied callers use `isTrialEligible(account.daysSinceSignup)` in trial
registration and `isRefundEligible(order.daysSincePurchase)` in refund handling.
Neither domain imports the other. No other files are changed or untracked.
This is a snapshot, not an executable checkout; tests/type/lint cannot be run.
