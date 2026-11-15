# R7

Review at revision A: Both toolbar and keyboard cancellation discard unsaved edits.
Suggested remedy: make discardEdits a no-op globally.

The UI contract at both revisions preserves edits on cancellation and discards them
on confirmed deletion. These are the complete action handlers.

## Revision A

```js
const onToolbarCancel = () => discardEdits();
const onKeyboardCancel = () => discardEdits();
const onConfirmDelete = () => discardEdits();
```

## Revision B (current)

```js
const onToolbarCancel = () => keepEdits();
const onKeyboardCancel = () => discardEdits();
const onConfirmDelete = () => discardEdits();
```

At both revisions keepEdits retains the draft and discardEdits clears it.
