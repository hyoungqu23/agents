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
FR-003 / AC-003: Show lookup failure separately from empty success. The user may select another tag, or explicitly retry the same tag. The selected tag is kept after failure. No automatic retry.

| Action or condition | Observable outcome | Next step or exit | Requirement |
| --- | --- | --- | --- |
| Lookup fails | Failure state, distinct from an empty result; the selected tag stays selected | User chooses another tag or retries | FR-003 / AC-003 |
| User selects another tag | New lookup for that tag | FLOW-001 | FR-003 / AC-003 |
| User explicitly retries the same tag | Same tag looked up again; selection unchanged | Success: FLOW-001 results or empty result. Failure: back to this flow | FR-003 / AC-003 |
| Failure occurs, no user action | No lookup is repeated automatically | Stays in failure state | FR-003 / AC-003 |

## Change history
- Revision 3: SRC-001 updated from revision 1 to revision 2, scoped to FR-003 / AC-003. Affected flow: FLOW-003 only (added explicit same-tag retry, selection preservation, no automatic retry). FLOW-001, FLOW-002, DEC-001, OD-001 and the unrelated plan are unchanged. No IDs were added, removed or reassigned.

## Unrelated plan
The mobile-app launch date is 2026-11-12 and remains tentative.
