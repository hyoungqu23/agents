# Review

Code review skills for Claude Code and Codex.

## Skills

| Skill | Description |
| --- | --- |
| [`review-pr`](skills/review-pr) | Review a GitHub pull request end to end: dedicated worktree, `review-code` delegation, approval, then inline comments posted as one review. |
| [`review-code`](skills/review-code) | Completion-gated hard review for PRs, branches, diffs, and working-tree changes. Inventories every changed file, routes stack specialists, and promotes only evidence-backed findings. |
| [`review-respond`](skills/review-respond) | Answer the review on your own PR: collect the threads waiting on you, verify each claim against the code, commit fixes as new commits, then post the approved replies inside the threads with commit links. Resolves nothing unless asked. |
| [`review-check`](skills/review-check) | 리뷰 지적 검증: check existing review claims against code and requirements without editing or posting; distinguish valid, partial, false-positive, and unresolved claims. |

Each skill is stored once under `skills/<skill>/` and shared by both platform manifests.

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
