---
id: flow:reading-notes
revision: 3
status: ready_for_review
sources:
  - id: SRC-001
    locator: requirements.md
    revision: 2
  - id: SRC-002
    locator: change.md
    revision: "supplied snapshot; revision unknown"
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
FR-003 / AC-003: When the user’s selected-tag lookup fails, show lookup failure separately from empty success and keep the selected tag. The user may explicitly retry the same tag, or select another tag to enter FLOW-001. Do not retry automatically. A successful same-tag retry shows only that tag’s stored notes; selecting a result enters FLOW-002. A successful retry with no matches shows an empty result and allows choosing another tag. If the retry fails, remain in FLOW-003 with the selected tag preserved and the same explicit retry or other-tag choices available.

## Unrelated plan
The mobile-app launch date is 2026-11-12 and remains tentative.

## Update history
- Revision 3: Inspected requirements.md revision 2 (SRC-001) and change.md (SRC-002). Updated only FLOW-003 / FR-003 / AC-003 behavior: explicit same-tag retry, selection preservation after failure, and no automatic retry. The prior source link was requirements.md revision 1; no flow or requirement IDs were retired or reassigned. FLOW-001, FLOW-002, DEC-001, OD-001, and the unrelated plan are unchanged.
- Status remains ready_for_review: the changed lookup-failure branch is specified and traceable; deletion remains undecided and outside scope. This update is not an independent review, gate pass, or implementation approval.
