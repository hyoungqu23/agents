# Review environment

- The change is a Vite + React component patch.
- No React, Vite, accessibility, or visual-review specialist skill is installed.
- Dependencies are not installed and network access is unavailable.
- The attached patch is the complete review scope; it is not a runnable checkout.

# Intent

Add an optional description below a project title. Empty descriptions should render nothing.

# Patch

```diff
diff --git a/src/projects/ProjectHeading.tsx b/src/projects/ProjectHeading.tsx
--- a/src/projects/ProjectHeading.tsx
+++ b/src/projects/ProjectHeading.tsx
@@ -1,3 +1,10 @@
-export function ProjectHeading({ title }: { title: string }) {
-  return <h1>{title}</h1>;
+type Props = { title: string; description?: string };
+
+export function ProjectHeading({ title, description }: Props) {
+  return (
+    <header>
+      <h1>{title}</h1>
+      {description ? <p>{description}</p> : null}
+    </header>
+  );
 }
```
