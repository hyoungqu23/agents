---
id: "flow:personal-tag-finder"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "current-prd.md"
    revision: "prd:personal-tag-finder revision 1; sha256 bd4111b943757670eb10fa9d9be5e84375f17f7af920d5c5e53e19e44d83ce28"
  - id: "SRC-002"
    locator: "clean-source.md"
    revision: "supplied snapshot 1; sha256 34e48200e92d3502e8e33f109af7ac6bb57c0652af761d8232b7e2320f1fce57"
  - id: "SRC-003"
    locator: "prior-review.json"
    revision: "unversioned; verdict ready_for_flow for sha256 b231647a...3334"
depends_on:
  - id: "prd:personal-tag-finder"
    revision: 1
---
# Personal tag finder — 사용자 흐름 명세

## Scope and freshness

- Actor: the owner (single personal user). Outcome: GOAL-001, find and open an existing note by an exact existing tag.
- In scope: FR-001, FR-002, FR-003, AC-001–AC-004.
- Constraints (DEC-001, PRD; matches SRC-002): personal use only; notes and tags already exist; no tag editing, sharing, new authentication, UI layout, storage design or numeric speed target.
- **Prior review is stale.** `prior-review.json` targets `current-prd.md` revision 1 with sha256 `b231647a…3334`; the file now hashes to `bd4111b9…ce28` with the same revision 1. Content changed without a revision bump, so its `ready_for_flow` verdict does not apply to the current text. It was not rerun, and it is not build approval.
- **Unsourced addition.** FR-003 and AC-004 sit after the PRD's "Next step" line. They are not in SRC-002, and the PRD's "no open decision" statement predates them. I carried them forward as written PRD requirements, not as a recorded user decision. Their provenance is unverified; confirm that the owner intends them (see Handoff).
- Assumption AS-001 (notes/tags are readable) is unverified. It is checked at integration and does not change these flows.

## Flows

### FLOW-001 — Find notes by tag and open one (FR-001, AC-001, GOAL-001)
Actor: owner. Entry: the owner has an existing tag to look up.

| Action or condition | Observable outcome | Next step or exit | Requirement |
| --- | --- | --- | --- |
| Owner selects an existing tag (e.g. alpha) | Exactly the notes carrying that tag are listed (N1, not N2 tagged beta) | Owner picks a note, or selects another tag (re-entry) | FR-001, AC-001 |
| Owner opens a listed note (N1) | N1's stored content is shown | Exit; owner may return to the result or choose another tag | AC-001 |
| Matches exist for the tag | Result contains only notes with that tag | — | FR-001 |

### FLOW-002 — Tag has no notes (FR-002, AC-002)
Entry: the owner selects an existing tag and the lookup succeeds with zero matches.

| Action or condition | Observable outcome | Next step or exit | Requirement |
| --- | --- | --- | --- |
| Lookup succeeds, zero notes | An identifiable empty result, distinct from failure | Owner selects another tag or exits | FR-002, AC-002 |

### FLOW-003 — Lookup fails; explicit retry (FR-002, FR-003, AC-003, AC-004)
Entry: the owner selects an existing tag and the lookup does not complete.

| Action or condition | Observable outcome | Next step or exit | Requirement |
| --- | --- | --- | --- |
| Lookup fails | Failure is reported, not shown as a successful empty result; the selected tag remains selected | Owner chooses to retry, selects another tag, or exits | FR-002, AC-003, FR-003 |
| Owner explicitly retries | Lookup runs again with the same tag only | Success → FLOW-001 or FLOW-002 outcome; failure → this flow again | AC-004 |
| No owner action | No automatic retry occurs | Stays in failure state | AC-004 |

Notes: whether the failure view offers other recovery or any retry limit is not specified. No retry count, backoff, error catalogue or message wording is invented.

## Coverage

| AC | Covered by | Note |
| --- | --- | --- |
| AC-001 | FLOW-001 | |
| AC-002 | FLOW-002 | |
| AC-003 | FLOW-003 | |
| AC-004 | FLOW-003 | Provenance of FR-003/AC-004 unverified (see above) |

Not covered (out of scope per DEC-001): tag editing, sharing, authentication, note creation. Not specified, so not flowed: partial results, access denial, stale data, cancellation. The source makes none of these relevant.

## Open items

- No OD-* open. Not an OD, but a check needed: confirm FR-003/AC-004 reflect the owner's intent, because they are not in SRC-002.
- AS-001: verify the supplied notes/tags are readable during integration. A failure there would surface as FLOW-003.

## Status and handoff

Status `ready_for_review`: the flows cover every in-scope AC and carry the unresolved items visibly. This is a draft, not an independent review or gate pass. The stale review should be replaced by a fresh prd-gate run on the current PRD if a gate is wanted.

For design: the designer may explore layout, how results/empty/failure are presented, and how retry is offered, provided the three outcomes stay distinguishable, the tag stays selected after failure, and retry happens only on explicit action. Layout and storage remain undecided.

## History

- Revision 1: initial flow from `current-prd.md` revision 1 (sha256 `bd4111b9…ce28`).
