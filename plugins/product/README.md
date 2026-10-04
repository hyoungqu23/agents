# Product

Product planning skills for Claude Code and Codex. The first stack provides problem
framing; subsequent PRs add PRD writing and review after their contracts are verified.

| Skill | Description |
| --- | --- |
| [problem-frame](skills/problem-frame) | 문제 정의: frame a product problem while preserving evidence, assumptions, user decisions, and unanswered questions. |

Use it for an idea, observed friction, or an update to an existing problem brief.
Brief advice stays in chat. Requested documents use the existing project convention
or docs/product/<slug>/problem.md. No external skill, CLI, automatic commit or posting
workflow is required. This version does not write PRDs or design implementation.

The [shared artifact contract](references/artifact-contract.md) defines stable IDs,
revision and provenance; [problem-template](references/problem-template.md) is an
adaptable outline. A completed draft is not proof of customer demand.

Evaluation inputs and rubrics live in skills/problem-frame/evals/evals.json.
Real model outputs must be inspected for unsupported claims and preserved source
qualifications; a manifest check or expected keyword alone cannot establish quality.

## Local validation

Run the repository validators and temporary marketplace load check, then the Python
unit tests. The first stack adds three focused CLI smoke cases:

```sh
python3 scripts/behavioral/run.py --model <model-id> --case problem-observed --case problem-hypothesis --case problem-update --output /tmp/new-problem-run
```

This consumes model capacity and uses synthetic inputs. Exact results and limits are
in `reports/problem-frame-2026-10-04/README.md` in the repository. The smoke does not
establish PRD writing/review, implicit discovery, Claude behavior or hosted CI.
