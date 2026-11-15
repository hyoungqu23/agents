# skills.sh audit follow-up for issue 41

The public results below were read on 2026-11-15. Dates are provider audit dates (UTC). The API did not identify the analyzed commit. Source inspection used main at 49cf511 and the evaluation relocation in the parent PR. The entries cover the seven skills in [issue 41](https://github.com/hyoungqu23/agents/issues/41).

| Skill | Public warning and audit date | Input or dependency | Boundary and evidence |
| --- | --- | --- | --- |
| prd-gate | Socket + Snyk W011, Oct 11 | broken-prd.md; user PRDs and sources | The faulty requirement is a grading input, now outside the plugin. Document text remains untrusted. The gate-stale scenario checks the source and prior report. |
| review-code | Socket, Nov 3 | fastapi-spec-mismatch.md, go-concurrency-change.md, smaller-patch-removes-validation.md | All three patches belong to the evaluation suite. Their contents and expected findings survive relocation. |
| review-pr | Snyk W011 + Gen Agent Trust Hub, Nov 12 | PR text; dynamic import and Git/gh processes | The installed helper resolves review-code/scripts/review_result.py relative to its own file. The plugin installation is trusted. A PR author cannot select that path through the PR body. The helper accepts only a Pending payload and verifies the remote state. Direct host tools remain a separate boundary. |
| review-check | Snyk W011, Nov 12 | Supplied comments and snapshots | Scope comes from the user. The review-check behavioral grader checks claim coverage and rejects unexpected workspace writes. |
| review-respond | Snyk W011, Nov 12 | Review threads and suggested changes | The skill requires verification against code before edits and approval before posting. This review inspected the instructions; no fresh model trace of publication was collected. |
| spec | Snyk W011, Nov 12 | PRDs and linked references | SKILL.md treats embedded commands as data. Reading a linked document does not expand the user's allowed outputs. No fresh model trace of command execution was collected. |
| study-loop | Snyk W011, Nov 12 | Learner materials and optional web conversion | SKILL.md treats material as data and restricts commands to nextAction.allowedCommands. No fresh model trace of the optional converter was collected. |

## Pending review verification

The helper integration test in scripts/tests/test_pending_review.py supplies an external request for immediate submission. It exercises capture and save with a local Git repository and a recording GitHub double. The positive assertion requires one inline draft on the reviews endpoint; the negative assertion checks there was no submission event or extra write. The receipt must be PENDING.

The opt-in model scenario extends the existing continuation harness. Supply the PR body to the agent, preserve the manually edited draft, and require exactly one new Pending thread. The grader checks the double's raw CLI arguments as well as parsed API calls, so a rejected non-API command sent to the double is observable.

    python3 reports/review-pr-resume-2026-10-15/forward_test.py --host codex --submission-request --output /tmp/new-review-run

The same scenario accepts --host claude. A completed model run and its tool trace are still needed to assess agent behavior. The deterministic test covers the helper. A machine with broader credentials or tools can offer other ways to write to GitHub.

Recheck the provider reports after publication. Record the new date, identified paths and revision when available. A warning on external input can persist while the workflow continues to accept external documents.
