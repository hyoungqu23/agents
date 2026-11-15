# Review context

Review this working-tree change. Request: omit archived projects from the existing
list while preserving order and leaving the input array intact. No API change.
The service already validates each project's ID and archived flag before calling
this function. Lists are limited to 200 entries by the existing endpoint.

Repository policy keeps small project operations in `src/projects/`. There is no
shared predicate/filter helper for this rule. The complete repository search
finds only `visibleProjects` and its two consumers, `ProjectList` and `ProjectMenu`.
Both consumers use the returned array as a list; neither depends on array identity.
There is no naming, length, or formatting rule violated by the implementation.

The previous review proposed a generic predicate interface, a registry for future
project filters, and renaming `items` to `projectCollection`. Those suggestions
were explicitly declined because there is one current rule, no requested filter
configuration, and the parameter's local meaning is clear. That decision's
assumptions still hold. Review findings remain subject to the actual code below.

## Patch

```diff
diff --git a/src/projects/visibleProjects.ts b/src/projects/visibleProjects.ts
--- a/src/projects/visibleProjects.ts
+++ b/src/projects/visibleProjects.ts
@@ -1,4 +1,4 @@
 type Project = { id: string; archived: boolean };
 export function visibleProjects(items: readonly Project[]): readonly Project[] {
-  return items;
+  return items.filter((item) => !item.archived);
 }
```

## Available tests

The existing Vitest cases exercise an empty input, all archived projects, and a
mixed list. They assert that IDs of visible projects retain their original order
and that the input array still contains every original entry. These cases cover
the requested behavior. The author reports that they passed; the reviewer has
not run them. This supplied snapshot is not an executable checkout.

There are no other changed, staged, unstaged, or untracked files. The review may
autofix safe mechanical issues, but no edits are explicitly requested.
