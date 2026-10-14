---
id: flow:reading-notes
revision: 2
status: ready_for_review
sources:
  - id: SRC-001
    locator: requirements.md
    revision: 1
depends_on: []
---
# Reading notes
DEC-001: Personal use only; tags and notes already exist.
OD-001: Deletion is outside this flow and remains undecided.

## FLOW-001 — Find notes
FR-001 / AC-001: Choose an existing exact tag. Show only its stored notes; selecting a result enters FLOW-002. Empty matches show an empty result and allow choosing another tag.

## FLOW-002 — Open a note
FR-002 / AC-002: Selecting a result opens that note's stored content. Closing it returns to the same filtered list.

## FLOW-003 — Failed lookup
FR-003 / AC-003: Show lookup failure separately from empty success. The user may select another tag.

## Unrelated plan
The mobile-app launch date is 2026-11-12 and remains tentative.
