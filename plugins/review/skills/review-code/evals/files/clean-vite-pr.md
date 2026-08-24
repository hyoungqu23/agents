# PR context

Title: Normalize project search terms

Body: Search should ignore surrounding whitespace and ASCII letter case. No API contract or UI behavior changes are intended.

Stack evidence from `package.json`:

```json
{
  "scripts": {
    "test": "vitest run",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "build": "vite build"
  },
  "dependencies": {
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "vite": "7.0.0",
    "vitest": "3.2.0"
  }
}
```

# Patch

```diff
diff --git a/src/projects/normalizeSearchTerm.ts b/src/projects/normalizeSearchTerm.ts
new file mode 100644
--- /dev/null
+++ b/src/projects/normalizeSearchTerm.ts
@@ -0,0 +1,3 @@
+export function normalizeSearchTerm(value: string): string {
+  return value.trim().toLowerCase();
+}
diff --git a/src/projects/normalizeSearchTerm.test.ts b/src/projects/normalizeSearchTerm.test.ts
new file mode 100644
--- /dev/null
+++ b/src/projects/normalizeSearchTerm.test.ts
@@ -0,0 +1,13 @@
+import { describe, expect, it } from "vitest";
+
+import { normalizeSearchTerm } from "./normalizeSearchTerm";
+
+describe("normalizeSearchTerm", () => {
+  it("trims surrounding whitespace", () => {
+    expect(normalizeSearchTerm("  Alpha  ")).toBe("alpha");
+  });
+
+  it("normalizes ASCII letter case", () => {
+    expect(normalizeSearchTerm("ALPHA-123")).toBe("alpha-123");
+  });
+});
```

Assume there are no other changed, staged, unstaged, or untracked files. The attached fixture is not a runnable checkout, so commands cannot actually be executed.
