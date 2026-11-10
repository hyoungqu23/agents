# agent-desktop / native input supplement

This is a candidate adapter; actual OS support must be established in the current
host. Inspect installed help/tool schema, OS permissions and target window bounds.
Bind the same browser window/profile used by the primary web tool. Accessibility
refs and coordinates belong to their actual session/window and fresh snapshot.

Record accessibility action versus physical keyboard/pointer input and actual
delivery status. Reobserve the business result after either action; a delivered key
or verified pointer position is not proof of saving/selection. If an action times
out after possible delivery, inspect current state before retrying any mutation.

Use supported atomic modifier+click operations when available. Do not hold a key in
one stateless command and assume another command sees it. Keyboard verification
needs real focus traversal, not only programmatic focus or synthetic DOM events.

Use OS dialogs only in the task's permitted scope. If focus/permission is wrong,
report the execution prerequisite and continue independent web checks. Native tools
may lack HTTP/DOM diagnostics; use actual available web evidence or retain that gap.
Session labels do not isolate OS focus. Never blanket-close the user's apps/windows.
