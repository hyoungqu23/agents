---
id: "prd:personal-tag-finder"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "clean-source.md"
    revision: "supplied snapshot 1"
depends_on: []
---
# Personal tag finder

EV-001: The owner requests finding existing reading notes by exact existing tags.
DEC-001: Personal use only. Notes and tags already exist. No tag editing, sharing,
new authentication, UI layout, data storage design or quantitative speed target.
GOAL-001: Find and open an existing note associated with the selected exact tag.
FR-001: Selecting an existing tag returns exactly the notes carrying that tag.
AC-001: Given N1 tagged alpha and N2 tagged beta, selecting alpha returns N1 and
not N2. Opening N1 shows N1's stored note content.
FR-002: Empty matches and lookup failure are distinguishable.
AC-002: A selected tag with no notes produces an identifiable empty result.
AC-003: A failed lookup is reported as failure, not as a successful empty result.
AS-001: The supplied notes/tags can be read; verify this during integration.
This nonblocking integration assumption does not change the select/open/empty/failure
user flows. No user policy decision remains open for the declared next step.
Next step: design these user flows, not architecture or implementation.
