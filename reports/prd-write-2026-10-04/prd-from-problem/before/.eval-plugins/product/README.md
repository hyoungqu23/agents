# Product

Product planning skills for Claude Code and Codex. The first two stacks provide problem framing and PRD drafting; independent PRD
review remains a subsequent change.

| Skill | Description |
| --- | --- |
| [problem-frame](skills/problem-frame) | 문제 정의: frame a product problem while preserving evidence, assumptions, user decisions, and unanswered questions. |
| [prd-write](skills/prd-write) | 제품 요구사항 작성: consume a problem frame or direct input, preserve source/decisions, and write observable requirements and acceptance criteria. |

Use problem-frame for an idea, observed friction, or an update to an existing problem brief.
Brief advice stays in chat. Requested documents use the existing project convention
or docs/product/<slug>/problem.md. No external skill, CLI, automatic commit or posting
workflow is required. prd-write handles requested PRD drafts and scoped updates; this version does not
design implementation or perform an independent PRD gate.

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

PRD drafts use the [PRD starting structure](references/prd-template.md), keep EV/AS/DEC/OD
identity from the problem frame, and add GOAL/FR/AC links. Unknown policies are not
settled by defaults. A direct requirements request does not require a fabricated
problem.md or a prior problem-frame invocation.
