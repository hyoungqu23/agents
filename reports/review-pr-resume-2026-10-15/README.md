# Pending review continuation (A3)

This evaluation checks continuation of an existing Pending review, preserving its
comments and manually edited summary while adding a newly verified finding. GitHub
is a local `gh` double; no real review comments were created, edited or submitted.
Real model calls used synthetic code and the review/content plugin instructions.

## Results

| Run | Persistence result | Workflow observation |
| --- | --- | --- |
| [Codex / gpt-6-astra](codex/result.json) | Passed: one Pending thread, no duplicate, old comment/summary/source preserved | Loaded review-code and applied it in the same invocation; no independent reviewer claimed. |
| [Claude initial environment attempt](claude-env-failure/result.json) | Not exercised; no API writes | Shell-variable permission checks rejected the helper command. Kept as a failed attempt. |
| [Claude with fixed helper wrapper](claude-first-continuation/result.json) | Passed the original persistence checks | Skipped loading review-code. The original result is retained; this is not a full skill-workflow pass. |
| [Claude after entrypoint clarification](claude-final/result.json) | Passed, including the added review-code loading check | Loaded review-code; reported incomplete coverage of its detailed gate and no un-ai wording pass. This validates continuation behavior, not the entire review-code workflow. |

Both successful hosts identified the permission predicate regression, retained
comment 101 verbatim, omitted the manually edited summary from the payload and
created only comment 102 through `addPullRequestReviewThread`. They verified the
existing review ID 91 remained Pending on its original commit. Claude's final pass
also corrected its earlier P0 severity to P1. The saved final responses and exact
payloads show the actual wording and declared verification limits.

The wrapper correction only sets a fixed PATH to the local API double. No sandbox,
network or permission boundary was widened. The review-pr clarification explicitly
requires loading review-code on continuation. Codex already did so before that
clarification. A final helper change unified stale/conflict status classification;
it was covered by integration tests after these model runs. Each run retains its
evaluated instruction hashes; `final-source-hashes.json` identifies the final files.

## Deterministic coverage

The local Git/CLI integration suite has 50 cases, including:

- Same-revision no-op and adding new Pending threads without event/submission.
- Lost create/append responses, partial batches and absence that cannot justify replay.
- Manual edits, deletions, regenerated keys, summary preservation and withdrawn findings.
- Concurrent local writers, remote edits during a batch and a remote exact addition.
- New head/base, empty clean reviews with stale targets, changed source and final readback.
- Recreated worktrees, missing receipts, v0.5 receipt migration and account/target binding.
- Paginated comments and the actual legacy review-comment listing response, resolved
  through the modern comment-detail GET instead of guessing file lines from positions.

Independent read-only review found the batch conflict/duplicate races, a missing
empty-result target check and the legacy listing mismatch. Those cases were fixed
and regression-tested. The listing mismatch was also checked against public GitHub
data with read-only requests; it was not a live Pending-write test.

Repository validation before PR: the full Python suite passed 92 tests before the
final status-readback regression was added; the final focused suite passed 50 tests.
Node fixture tests passed 3/3. Both official plugin validators, skill validation,
reference/frontmatter checks and CLI load checks passed. CI runs the final complete
suite (93 Python tests) on the PR.

## Reproduction and evidence

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p test_pending_review.py
# Only with authorization for synthetic model-service calls:
python3 reports/review-pr-resume-2026-10-15/forward_test.py --host codex --output /tmp/a3-codex-new
python3 reports/review-pr-resume-2026-10-15/forward_test.py --host claude --output /tmp/a3-claude-new
```

The harness seeds a previously saved finding, changes the summary as a user would,
and supplies the remaining raw code for review. Expected outcomes are outside the
model prompt. The API double denies every mutation except Pending creation and
Pending-thread addition. It returns the legacy comment-list shape during forward tests.

Per-run artifacts retain raw result JSON, prompts, final responses, API calls,
receipts, exact drafts and instruction/source hashes. `tool-calls.json` is a compact
extraction of command/tool inputs and success/error metadata; full tool outputs and
stream traces remain in the local `/private/tmp/hm2-review-resume-*-20261015` runs.
The initial Claude failure has no draft artifacts. Earlier result files were not
rewritten when the rubric was tightened.

These tests do not establish live GitHub Pending permissions, full cross-host review
quality, every qualitative scenario on both models, cross-device exactly-once
semantics, or immunity to another actor submitting the review between reads.
New-commit continuation intentionally produces a local reassessment plan and keeps
the older Pending intact; it does not repin or replace that review.
