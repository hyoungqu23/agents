# PRD review contract

## Review lenses

These are this plugin's product criteria, not a claim of equivalence to a company's
R1–R5. Apply more specific supplied project rules within their actual scope.

| Lens | Inspect |
| --- | --- |
| R1 — Problem/evidence | Is the stated problem supported or honestly hypothetical? Has evidence been altered to justify a solution? |
| R2 — User/outcome | Are user scope and intended outcomes consistent with supplied context? |
| R3 — Scope/acceptance | Are material requirements observable, bounded and coherent? Are important scenarios missing or contradictory? |
| R4 — Boundaries/constraints | Are exclusions and explicit decisions preserved? Are invented technical choices masquerading as necessities? |
| R5 — Decisions/traceability | Are sources and dependencies current? Are consequential unknowns and stale reviews visible? |

Mark each lens assessed or not_assessed and explain limitations. Evaluate meaning,
not section names or a mandatory Given/When/Then syntax. Missing numeric targets are
not defects when the user outcome can be observed without them.

## Candidate evidence gate

A candidate is confirmed only when an inspected passage supports the concern, a
source/constraint or internal inconsistency establishes why it is wrong, and the
next-step impact is specific. Cite file plus line/section/FR/AC and a short quote or
content anchor. Assign stable finding IDs within the report. Avoid invented line
numbers, owners, severity, policies or approval claims.

Keep verified findings separate from unresolved evidence questions and refuted
candidates. Refuted candidates need only be listed when raised by the user or a prior
review; no need to pad a clean review with imaginary concerns. User acceptance of a
real issue records authority and residual impact; it does not refute the evidence.

## Overall disposition

- ready_for_flow: assessed scope has no unresolved blocker to the declared user-flow
  design. Bounded nonblocking assumptions may remain. This is not build approval.
- revise: confirmed document omission/contradiction needs authoring correction.
- needs_decision: an actual unresolved product/policy choice changes the next flow.
- incomplete: required evidence or review execution is unavailable, so an overall
  judgment cannot be finished. State what was and was not assessed.

When several conditions apply, list them all. Do not report ready_for_flow if any
required lens/input or next-step blocker is unresolved. Use incomplete for a critical
assessment gap; otherwise revise for a confirmed defect, otherwise needs_decision
for blocking choices, otherwise ready_for_flow. An upstream draft status alone does
not determine this verdict. Explain relevance to the specific next step.

## Saved reports and freshness

Markdown reports record the target ID/revision and, when available, SHA-256 of the
actual bytes read; sources/dependency identities and their known content/version;
R1–R5 coverage; findings with location/evidence/impact/action; open decisions;
unresolved/refuted supplied claims; limitations and overall disposition.
Never fabricate a digest. If hashing or revision comparison is unavailable, declare
freshness unverified rather than claiming a reusable verdict. An old report is valid
only for its recorded content and review boundary; changed target/source content
requires reassessment, including when the nominal revision is unchanged.

When JSON is explicitly requested, use this compact companion structure:

```json
{
  "target": {"path": "prd.md", "id": "prd:example", "revision": 1, "sha256": "actual digest"},
  "sources": [{"path": "notes.md", "identity": "known revision or unknown", "sha256": "actual digest or null", "read": true}],
  "verdict": "ready_for_flow",
  "coverage": [{"lens": "R1", "status": "assessed", "note": "actual scope and limitation"}],
  "findings": [{"id": "F-001", "lens": "R3", "disposition": "confirmed", "location": "prd.md / AC-001", "evidence": ["inspected passage and basis"], "impact": "specific next-step effect", "action": "correction or decision"}],
  "open_decisions": [{"id": "OD-001", "blocking": false, "impact": "bounded effect", "question": "actual choice"}],
  "claims": [{"id": "prior supplied concern", "disposition": "refuted", "evidence": ["actual basis"]}],
  "prior_review": {"status": "none", "reason": "no prior report supplied"},
  "independence": "self_review, separate_invocation, or unverified, with actual basis",
  "limitations": ["actual unassessed area"]
}
```

Include all five coverage lenses. Use empty arrays when appropriate; the finding above
is a shape example, not a requirement to find one. Unknown ID/revision/digest is null
with a reason, never copied example content. prior_review.status is none, current,
stale, or unverified. This is an output convention, not an implemented schema validator.
