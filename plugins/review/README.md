# Review

Code review skills for Claude Code and Codex.

## Skills

| Skill | Description |
| --- | --- |
| [`review-pr`](skills/review-pr) | Review a GitHub PR read-only, then save or resume a commit-pinned **Pending review**, preserving existing drafts. Never submits. |
| [`review-code`](skills/review-code) | Completion-gated hard review for PRs, branches, diffs, and working-tree changes. Inventories every changed file, routes stack specialists, and promotes only evidence-backed findings. |
| [`review-respond`](skills/review-respond) | Answer the review on your own PR: collect the threads waiting on you, verify each claim against the code, commit fixes as new commits, then post the approved replies inside the threads with commit links. Resolves nothing unless asked. |
| [`review-check`](skills/review-check) | 리뷰 지적 검증: check existing review claims against code and requirements without editing or posting; distinguish valid, partial, false-positive, and unresolved claims. |

Each skill is stored once under `skills/<skill>/` and shared by both platform manifests.

## Pending PR comments

`review-pr` always leaves comments **Pending (미제출)**. It does not send a COMMENT,
APPROVE or REQUEST_CHANGES event, submit a draft, or deliver findings as individual
comments/replies. The user can inspect the Pending review in GitHub.

The bundled `pending_review.py` captures a clean detached PR target and checks the
source, diff anchors and current base/head before writing. It pins commit_id, omits
event and reads the result back to verify PENDING with no submitted_at. A target
change during creation is reported as a stale draft; there is no automatic replay,
relocation, submission or replacement of an existing Pending review.

On continuation, it reconciles a durable receipt with all remote comments. Same-head
reruns deduplicate; new findings append to the existing Pending review. Manual edits,
deletions, changed findings and summaries are preserved and returned as conflicts.
Interrupted writes require positive readback before continuing. A new head gets a
local reassessment plan while the older Pending stays intact: this version does not
repin reviews or move draft anchors. See [resume and recovery](skills/review-pr/references/resume.md)
for supported behavior, migration from v0.5, and macOS/Linux journal requirements.

PR review and all specialists are report-only. Head-side instructions and scripts
remain review input; trusted base rules and actual host execution controls govern
the review. See [the shared boundary](references/pr-review-boundary.md).
The helper's Git checks detect visible checkout changes; they are not an OS sandbox.

Git-backed `review-code` reviews now produce a structured result outside the source.
The checker compares current SHAs, the real changed-file inventory and exact source
quotations, then returns complete, partial or invalid. Missing coverage and unresolved
work stay visible. See [the result contract](skills/review-code/resources/review-result.md).

From 0.7.0, `review-pr save` requires `--review-result`; old receipts can still be
inspected and recovered. Draft comments must match eligible finding IDs, anchors and
text. A supported finding may be saved from a partial review, whose partial status is
preserved in the receipt. Saving Pending is not a claim that the entire review is done.
The checker cannot certify reasoning quality or whether claimed commands really ran;
the focused [cross-host evaluation](../../scripts/behavioral/README.md#structured-review-completion-on-both-hosts)
tests actual findings, false positives and scope reporting on synthetic cases.
The [completion evaluation record](../../reports/review-completion-2026-10-16/README.md)
includes both hosts' outputs, initial fixture errors and remaining limits.

`review-code` always checks cohesion, coupling, duplicate implementations of the
same rule, repository patterns and applicable best practices, and naming. Tests
passing does not exempt a concrete maintenance defect. Findings identify the
existing owner or implementation and the smallest useful fix; independently
owned policies that only look alike do not require a shared abstraction.

Before recommending or autofixing a change, the review weighs the cost of leaving
the code against the smallest complete remedy and its complexity and regression
risk. Adequate code can stay unchanged; optional cleanup cannot block a merge.
Required safety checks and behavior tests remain intact. This restraint draws on
[Ponytail's approach](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md).

`review-code` and `review-respond` polish PR comment text with `un-ai` from the [`content`](../content) plugin. Install both plugins for that pass; without `content`, the skills apply their comment wording rules directly and report the missing pass.

## Behavioral evaluation

[PR #16 and #17 evaluation evidence](../../reports/review-code-evaluation-2026-10-11/report.md) records the fixed commits, model, paired scenarios, outputs, and limitations. Both old and updated instructions passed the selected cases; the result does not establish a general detection improvement. The same cases are reused to check the consolidated guidance.

## Checking an existing review

Use `review-check` for requests such as “Claude가 남긴 이 리뷰가 맞는지 확인해줘.”
It accepts pasted claims or a review file plus a repository/ref or supplied snapshot.
It reports valid, partially valid, false-positive, and unresolved claims with evidence,
and distinguishes a historically valid finding from a fix already present today.
It does not edit code or post replies. A requested saved report includes a JSON
companion; an ordinary check answers in the conversation without writing files.

The shared [claim verification procedure](references/claim-verification.md) also
supports `review-respond`, whose fix and reply workflow remains separate.
Run the focused behavioral smoke with:

```sh
python3 scripts/behavioral/run.py --model <model-id> --case review-check --output /tmp/review-check-unique-run
```

The six scenarios in `skills/review-check/evals/evals.json` are a qualitative rubric;
the smoke executes scenario 5 only. It does not establish full scenario coverage,
automatic discovery, Claude behavior, or the absence of regressions in PR posting.

## Pending-review validation

The repository Python suite includes a local bare Git remote and a `gh` API double
for Pending creation, source/head changes, invalid anchors, existing drafts and
uncertain writes. No live GitHub comments are required for those tests. Actual
model forward-test results and limits are recorded in
[the Pending review evaluation](../../reports/review-pr-pending-2026-10-14/README.md).
Continuation tests and model-run limits are recorded in
[the A3 evaluation](../../reports/review-pr-resume-2026-10-15/README.md).
