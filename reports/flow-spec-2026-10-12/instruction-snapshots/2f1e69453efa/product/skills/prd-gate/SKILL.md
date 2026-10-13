---
name: prd-gate
description: Review a PRD against its problem, sources and decisions before user-flow design. Check evidence, user outcomes, scope, observable acceptance, boundaries and revision freshness without rewriting the input. Use when asked to review a PRD, assess readiness for flow design, or recheck changed requirements. Do not use for drafting a PRD (prd-write), code review, implementation, or technical/screen design.
---

# PRD Gate

The Korean label is **제품 요구사항 검토**. Review the document as supplied, with
its real context. This is a product-readiness opinion, not a deployment or build approval.

Read [artifact-contract.md](../../references/artifact-contract.md) for source and
claim meanings, then [prd-review-contract.md](../../references/prd-review-contract.md)
for review lenses, dispositions, evidence and saved-output conventions.
No external CLI or installed sibling skill is required for ordinary review.

## Establish the review boundary

Read the PRD, available problem/source/decision inputs and applicable project criteria.
Direct entry is valid: an existing PRD need not have a problem-frame invocation.
Do not create a missing upstream artifact or impose this plugin's document format.
Record the actual target ID/revision or explicitly unknown metadata, and content
identity when tools permit. Referenced inputs that cannot be read remain unverified.
Distinguish a critical missing source from irrelevant or optional background.

A prior report is evidence of a past review, not authorization to reuse its verdict.
Compare target and dependency identities/content before relying on it. Changed content
invalidates the prior report even if someone forgot to increment revision. Reassess
changed claims and affected dependencies; stale ready_for_flow never carries forward.

## Inspect and verify

Apply R1–R5 to the declared boundary. Look for material problems rather than a quota
of findings. Separate an observed/documented fact, assumption, explicit authority's
decision and open choice. A personal tool does not need invented market research,
numeric targets or a new authentication system to make its requirements reviewable.

Every confirmed finding needs an exact target location, inspected supporting evidence
and a concrete impact on the declared next step. Check each candidate against the
source and exclusions before reporting it. A disproven concern is refuted, not a
user-accepted defect; a concern whose evidence is unavailable stays unresolved.
Recommendations must not become new decisions. Avoid demanding UI/API/database design
as a prerequisite for assessing a PRD's user outcomes.

Unknown behavior is not automatically an authoring defect. If a real user decision
changes the next flow, identify the alternatives and effect without choosing a default.
If an assumption is bounded and does not change that next step, retain it as nonblocking.
Explain which concrete flow work can or cannot proceed. Ask focused questions only
when they affect the verdict; honor a no-questions review and leave open choices visible.

## Report and stop

Default to a conversational result. Save only when requested, at the requested path
or existing convention, otherwise `docs/product/<slug>/prd-review.md`. Include target
identity, read sources, lens coverage, verified findings, open choices, unassessed
areas and the overall disposition. Use the saved report convention when JSON is requested.
An empty findings list is valid for a clean document.

Review is read-only with respect to the PRD and its inputs. Do not rewrite requirements,
change metadata/status, implement, commit, publish or launch a next phase as part of
review. If the user also explicitly authorized fixes, distinguish the review of the
original from the changed document and re-review the latter; never present the earlier
verdict as applying to an edited revision.

Declare whether this was self-review, a separate invocation, or independence unverified.
When author invocation history is unavailable, mark it unverified; merely receiving
an existing document does not establish separation from its author. Do not claim independent
review because a role label or another section was used. In an explicitly requested
multi-stage workflow, the coordinator may call the author and reviewer separately
when that facility is available and authorized. If unavailable or failed, record the
limitation and return incomplete when the requested independence cannot be met.
Do not silently replace a required reviewer with self-scoring or bypass service limits.
