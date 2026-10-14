---
id: flow:reading-notes
revision: 3
status: ready_for_review
sources:
  - id: SRC-001
    locator: requirements.md
    revision: 2
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
FR-003 / AC-003: When the user's lookup fails, show lookup failure separately from empty success and keep the selected tag. The user may select another tag, returning to FLOW-001, or explicitly retry the same selected tag. Do not retry automatically. A successful retry returns to FLOW-001 with that tag's stored notes or an empty result; selecting a result enters FLOW-002. If the retry fails, remain in FLOW-003 with the selected tag preserved and the same choices available.

## Unrelated plan
The mobile-app launch date is 2026-11-12 and remains tentative.

## Change history
Revision 3: Applied change.md using SRC-001 (requirements.md) revision 2. Only FR-003 / AC-003 and FLOW-003 behavior changed: explicit same-tag retry, selection preservation after failure, and no automatic retry. FLOW-001, FLOW-002, DEC-001, OD-001, and the unrelated plan are unchanged. Status remains ready_for_review because the affected flow covers the updated acceptance criterion without a blocking policy choice; this is not an independent review or build approval.
