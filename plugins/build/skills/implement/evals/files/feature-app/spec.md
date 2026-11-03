# Project list implementation

- AC-1: Add a labelled status selector above the list: All, Active, Archived, Paused.
  Changing it fetches that status through the existing API client and shows matching
  projects and their result count. Use the selected reference's structure.
- AC-2: A project can be selected and its name appears in the selected-project panel.
  Keep the selection when filtering hides that project. Filtering back restores the
  selected appearance. A successful empty result has its own visible empty state.
- AC-3: A failed request has the existing error treatment and Retry action, distinct
  from an empty success. Retry uses the current filter and preserves the selection.
  The current implementation must not be reported browser-verified without opening it.

Use DESIGN.md and ux.md. Implement in src/ and tests/. The server and contracts are
provided infrastructure. Do not commit, push, post, install packages, or edit the
input documents/user draft. Record evidence outside this application.
