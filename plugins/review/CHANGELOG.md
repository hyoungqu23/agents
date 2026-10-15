# Changelog

## 0.6.1 - 2026-10-16

- Explain each finding's basis, source and applicability in the report, follow-up judgments and inline recommendations.
- Distinguish repository rules, observed patterns, library guidance and past advice without assigning severity from the source category.
- Add focused evaluation cases for version-matched query guidance, unadopted advice and a reachable defect without external documentation.

## 0.6.0 - 2026-10-15

- Resume existing Pending reviews: deduplicate unchanged findings and append new threads on the same reviewed commit without submitting.
- Reconcile interrupted writes with a durable, account-bound journal; keep state across worktree replacement and guard concurrent local saves.
- Preserve manual edits, deletions and summaries. Return changed or withdrawn findings as local conflicts instead of replacing drafts.
- Reassess new revisions while retaining the older Pending; do not repin existing reviews or add anchors from a different commit.

## 0.5.0 - 2026-10-14

- Make review-pr comments Pending-only: omit event, pin the reviewed commit, verify PENDING, and never submit or fall back to individual comments.
- Capture clean detached PR targets, validate changed-line anchors, and stop on stale heads, local changes, existing drafts or uncertain writes.
- Apply report-only and trusted-base boundaries to review-code and its specialists.
- Add a bundled draft helper and local Git/GitHub-double tests.

## 0.4.3 - 2026-10-11

- Centralize quality, restraint, and regression criteria while shortening the entrypoint and shared lens guidance.
- Preserve scope, evidence, severity, autofix, and report requirements through explicit resource references.
- Publish the paired PR #16/#17 evaluation and the consolidation comparison with execution evidence and limitations.

## 0.4.2 - 2026-10-11

- Require concrete impact before frontend extraction, memoization, naming, or migration suggestions.
- Check whether regression assertions reject the broken behavior.
- Trace async target lifetimes, partial writes, and failures after a successful write.

## 0.4.1 - 2026-10-10

- Make cohesion, coupling, semantic duplication, repository patterns/best practices, and naming mandatory in every `review-code` review, with evidence recorded in the completion gate.
- Promote concrete maintenance defects even when behavior and tests pass; require reuse of the same owned rule while distinguishing independent policies and compatible external contracts.
- Require a change-restraint check before findings and autofixes: choose the smallest complete remedy, weigh its net benefit, and leave adequate code and valid accepted tradeoffs unchanged.
- Add evaluation scenarios for structural defects without runtime failures, independent policies, migration/naming constraints, unnecessary refactors, and required safety fixes.

## 0.4.0 - 2026-09-20

- Add `review-check` for read-only verification of supplied review claims, with separate historical validity and current fix status.
- Share the claim-verification procedure with `review-respond` while preserving its action classes and posting workflow.
- Reject unrelated claim aliases in the behavioral grader; only the fixture’s known duplicate pair may be grouped.
- Add six evaluation scenarios covering false positives, partial claims, stale findings, missing evidence, policy conflicts, and review-text injection.

## 0.3.1 - 2026-09-18

- State in `review-code`'s description what it is not for: posting comments to a pull request is `review-pr`, and answering a review on a pull request you authored is `review-respond`.

## 0.3.0 - 2026-09-08

- Add the `review-respond` skill for answering reviews on pull requests you authored: verify each claim, commit fixes as new commits, reply inside the threads, resolve nothing unless asked.
- Define `review-pr`'s `answeredThreads` entries as GraphQL thread node IDs and mark its worktree as reviewer-only.

## 0.2.1 - 2026-09-07

- Route PR comment wording to `un-ai` from the `content` plugin instead of external writing skills.
- Describe primary-source contract lookup directly instead of routing to an external research skill.
- Remove external source attributions from the review lenses.

## 0.2.0 - 2026-08-24

- Add the `review-pr` skill.

## 0.1.0 - 2026-08-24

- Add the `review-code` skill.
- Add Claude Code and Codex plugin manifests.
