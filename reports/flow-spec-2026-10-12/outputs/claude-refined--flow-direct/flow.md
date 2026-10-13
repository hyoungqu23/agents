---
id: "flow:personal-reading-notes"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "direct-input.md"
    revision: "supplied snapshot; sha256 d6884767471b91c1548ce2c083463a58f387a2b250da71fc7bba9a139f649955; VCS unknown"
depends_on: []
---

# 사용자 흐름 명세: Personal reading notes

Direct input only. No PRD, FR/AC IDs, prior review, or upstream documents exist (SRC-001 states "No prior documents exist"), so none are referenced. Source anchors are used instead: `SRC-001#goal`, `#empty-vs-failure`, `#failure-recovery`, `#context`, `#exclusions` (labels for the sentences of direct-input.md, not edits to it).

## Scope

- Actor: the single personal user (SRC-001#context: personal use).
- Outcome: choose an existing exact tag, see only that tag's stored notes, open a note (SRC-001#goal).
- Context (EV-001, SRC-001#context): tags and notes already exist, so creating them is not part of this flow.
- Excluded (DEC-001, SRC-001#exclusions): note editing, sharing, new authentication, storage design, speed target. The flow does not add them.

## Source anchors (stand in for AC)

| Anchor | Statement |
| --- | --- |
| A1 `#goal` | Choose an existing exact tag |
| A2 `#goal` | See only that tag's stored notes |
| A3 `#goal` | Open a note |
| A4 `#empty-vs-failure` | Empty results and a failed lookup are visibly different |
| A5 `#failure-recovery` | On failure the user can choose another tag |

## FLOW-001: Browse notes by tag and open one

Actor: personal user. Entry: the user wants to read notes under a tag that exists.

| Action or condition | Observable outcome | Next step or exit | Source |
| --- | --- | --- | --- |
| User chooses an existing exact tag | Lookup of that tag's notes starts | Lookup succeeds with notes, is empty, or fails | A1 |
| Lookup succeeds and the tag has stored notes | Only notes stored under that exact tag are shown; none from other tags | User opens a note (below) or chooses another tag | A2 |
| User opens a shown note | The note's content is shown | Exit; user may return to the tag's notes or choose another tag (return mechanics not specified; see OD-002) | A3 |
| Lookup succeeds but the tag has no stored notes (empty success) | An "empty" state, visibly distinct from the failure state | User can choose another tag (see OD-001) | A4 |
| Lookup fails | A "failed" state, visibly distinct from the empty state; no notes presented as if the tag were empty | User chooses another tag, re-entering FLOW-001 at the first row | A4, A5 |

## Distinguishing empty from failure (A4)

- Empty = the lookup completed and found zero stored notes. Failure = the lookup did not complete. The user must be able to tell which occurred without inferring it.
- Visual form (text, icon, color, layout) is left to design; only the distinguishability is required.

## Coverage

| Anchor | Covered by |
| --- | --- |
| A1 | FLOW-001 row 1 |
| A2 | FLOW-001 row 2 |
| A3 | FLOW-001 row 3 |
| A4 | FLOW-001 rows 4 and 5 |
| A5 | FLOW-001 row 5 |

No anchors are uncovered. Non-interactive items: none identified.

## Open decisions (nonblocking)

- OD-001: Whether the empty state offers a way to choose another tag. The source only requires this on failure (A5). Not assumed. Affects the empty-success row; the core flow and the empty/failure distinction are unaffected. Revisit when design or the user states the empty-state behavior.
- OD-002: How the user returns from an opened note, and how the tag is chosen (typed vs. picked). The source says "exact tag" and "choose" but not the input control. Left to design; not assumed.
- OD-003: What counts as a failed lookup (e.g. which conditions, and whether retrying the same tag is offered). The source only requires that the user can choose another tag. No retry policy or error catalogue is invented here.
- OD-004: Behavior when the chosen tag does not exist or has no exact match. The source says tags exist and the user chooses an existing one, so this is not modeled as a flow; whether it falls under "failure" or "empty" is unspecified.

## Assumptions

- AS-001: "Exact tag" means exact-match selection, not partial or fuzzy search. Reason: literal reading of SRC-001. Impact: if search is wanted, FLOW-001 row 1 changes. Check: confirm with the user.

## Handoff

- Design can explore: how a tag is chosen, how notes are listed, how empty and failed states look, how a note opens and the user returns.
- Requires a product choice: OD-001 through OD-004.
- Constraints to carry: DEC-001 exclusions; empty and failure must be visibly different; failure must allow choosing another tag.
- Status `ready_for_review`: the declared flow is complete with bounded, nonblocking unknowns. This is not an independent review or gate pass and is not approval to build. No visual variant was chosen.

## History

- Revision 1: initial draft from direct-input.md; no questions asked, per the request.
