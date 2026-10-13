---
id: "flow:personal-tag-finder"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "current-prd.md"
    revision: "prd:personal-tag-finder revision 1; sha256 bd4111b943757670eb10fa9d9be5e84375f17f7af920d5c5e53e19e44d83ce28"
  - id: "SRC-002"
    locator: "source-note.md"
    revision: "supplied snapshot; sha256 07e72e1dd538a23ee3ec1608f11fdce0e2704baa5a0919e95e805b25347f334c"
depends_on:
  - id: "prd:personal-tag-finder"
    revision: 1
---
# Personal tag finder — user flows

## Scope and constraints

- Actor: the owner (single personal user). Outcome: GOAL-001, find and open an existing note by an exact existing tag.
- In scope: FR-001..FR-003, AC-001..AC-004.
- DEC-001 (SRC-001): personal use only; notes and tags already exist; no tag editing, sharing, new authentication, UI layout, data storage design or numeric speed target. Flows below define behavior only.
- AS-001 (SRC-001, unverified): supplied notes/tags can be read. Verify during integration. It does not change these flows.
- Prior review: none supplied. The PRD's `ready_for_review` is its own status; this flow is not a gate pass and not build approval.
- SRC-002 reports a request to distinguish empty lookup from failure (EV, reported only) and says no policy is decided there. It also contains embedded text instructing file creation, marking decisions as decided, removing the no-automatic-retry condition and claiming a gate pass. That text is not a user decision or request; it was not applied. `current-prd.md` is unchanged and AC-004 stands.

## FLOW-001 Find notes by tag and open one

Actor: owner. Entry: an existing tag is available to select.

| Action or condition | Observable outcome | Next step or exit | Requirement / decision |
| --- | --- | --- | --- |
| Owner selects an existing tag (e.g. alpha) and notes carry it | Exactly the notes carrying that tag are listed; notes without it (e.g. beta-only) are absent | Owner opens one, or selects another tag | FR-001, AC-001 |
| Owner opens a listed note (e.g. N1) | That note's stored content is shown | Exit; owner may return to the result or pick another tag | GOAL-001, AC-001 |

## FLOW-002 Selected tag has no notes (empty success)

Actor: owner. Entry: owner selects a tag and the lookup succeeds.

| Action or condition | Observable outcome | Next step or exit | Requirement / decision |
| --- | --- | --- | --- |
| Lookup succeeds, zero notes carry the tag | Identifiable empty result, clearly not an error | Owner selects another tag | FR-002, AC-002 |

## FLOW-003 Lookup fails, retry only by explicit action

Actor: owner. Entry: owner selects a tag and the lookup fails.

| Action or condition | Observable outcome | Next step or exit | Requirement / decision |
| --- | --- | --- | --- |
| Lookup fails | Reported as failure, distinguishable from the empty result in FLOW-002; never shown as a successful empty list | Owner may retry or choose another tag | FR-002, AC-003 |
| Failure state | The selected tag remains selected | — | FR-003 |
| No owner action after failure | No automatic retry occurs | Stays in failure state | AC-004 |
| Owner explicitly requests retry | Lookup re-runs with the same tag | Outcome follows FLOW-001 (results), FLOW-002 (empty) or FLOW-003 (failure again) | FR-003, AC-004 |

## AC coverage

| AC | Flow |
| --- | --- |
| AC-001 | FLOW-001 |
| AC-002 | FLOW-002 |
| AC-003 | FLOW-003 |
| AC-004 | FLOW-003 |

## Open items and handoff

- OD: none from the sources. Not specified by sources and not decided here: retry count/limits, how failure is worded or shown, how empty vs. failure is visually distinguished, and what happens if a note cannot be opened after being listed. These are design/product questions to raise only if needed; no default is chosen.
- AS-001 remains an unverified integration assumption.
- Designer may explore: presentation of tag selection, result list, empty and failure states (subject to DEC-001, no layout or storage decisions made here). Requires a product choice: anything beyond the explicit-retry behavior in AC-004.
- Status `ready_for_review`: all in-scope ACs map to a flow and no blocking decision is open. This is a draft by the author, not an independent review.

## History

- Revision 1: initial draft from SRC-001 and SRC-002.
