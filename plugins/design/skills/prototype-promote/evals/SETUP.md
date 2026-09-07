# Evaluator setup

Read this before launching the executor. `files` contains only regular input paths,
relative to this skill directory. Copy those files to a new workspace, stripping
the group prefix in the table. Keep grading expectations out of executor context.

| Eval | Input group prefix | Required starting state |
| --- | --- | --- |
| 1, 2, 3, 5 | `evals/files/variant-board/` | Fresh source tree; no promoted reference |
| 4 | `evals/files/variant-board/` | Prepare the hand-edit rerun below |
| 6 | `evals/files/variant-board/` | Prepare the authority-change rerun below |
| 7, 8 | `evals/files/module-reference/` | Fresh module-based source tree; create an empty `apps/web/` |

## Reruns: prepare before the measured invocation

For evals 4 and 6, first invoke `prototype-promote` with this setup request:

> Select B from scratch/explore/index.html for apps/web/src/activity.txt and promote it to prototype/activity. Preserve the source and design documents and align app tokens.

Confirm that `prototype/activity/index.html` and `reference.md` were produced. Record
the initial source, authority and reference contents. A failed prerequisite is a
**setup failure**, not a passing or failing rerun; fix the prerequisite before proceeding.

- **Eval 4:** change only the visible detail-button label in the promoted HTML to
  `기록 자세히 보기`. Keep the original HTML, design documents and reference note unchanged.
- **Eval 6:** change only `apps/web/DESIGN.md`'s accent from `#185adb` to `#126345`.
  Keep source HTML, source assets and the promoted reference unchanged.

Now give the executor the eval's actual prompt and workspace. The recorded before/after
contents are evaluator evidence; do not give the executor the expected answer.

## Runtime cases

Eval 5 deliberately has no browser tools; no installation is authorized by that request.
For evals 7 and 8, the evaluator needs a browser with normal security settings. Test the
result using the opening mode requested in the prompt. Use a fresh preview process for
eval 8, not a server still running from setup. If no browser is available, record the
runtime assertion as not run rather than scoring a source inspection as a pass.
