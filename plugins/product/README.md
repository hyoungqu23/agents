# Product

Product planning skills for Claude Code and Codex. The three foundation skills provide problem framing, PRD drafting and read-only
readiness review for user-flow design.

| Skill | Description |
| --- | --- |
| [problem-frame](skills/problem-frame) | 문제 정의: frame a product problem while preserving evidence, assumptions, user decisions, and unanswered questions. |
| [prd-write](skills/prd-write) | 제품 요구사항 작성: consume a problem frame or direct input, preserve source/decisions, and write observable requirements and acceptance criteria. |
| [prd-gate](skills/prd-gate) | 제품 요구사항 검토: verify evidence, acceptance, boundaries, open decisions and target freshness before user-flow design. |

Use problem-frame for an idea, observed friction, or an update to an existing problem brief.
Brief advice stays in chat. Requested documents use the existing project convention
or docs/product/<slug>/problem.md. No external skill, CLI, automatic commit or posting
workflow is required. prd-write handles requested PRD drafts and scoped updates; prd-gate reviews readiness separately without rewriting input documents.

The [shared artifact contract](references/artifact-contract.md) defines stable IDs,
revision and provenance; [problem-template](references/problem-template.md) is an
adaptable outline. A completed draft is not proof of customer demand.

Evaluation inputs and rubrics live in each skill’s evals/evals.json.
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

The second stack adds three PRD smoke cases:

```sh
python3 scripts/behavioral/run.py --model <model-id> --case prd-from-problem --case prd-update --case prd-direct --output /tmp/new-prd-run
```

The upstream fixture is the preserved output of the first stack’s actual problem-frame
run. Results and limits are recorded in `reports/prd-write-2026-10-04/README.md`.


Use prd-gate directly on an existing PRD or after a requested draft. Results stay in
chat unless saving is requested. The [review contract](references/prd-review-contract.md)
defines dispositions, source-backed findings and stale-review handling. Ordinary
review needs no CLI or installed sibling skill; independent execution is reported
only when actually performed.

The third stack adds four isolated review cases and one explicitly requested chain:

```sh
python3 scripts/behavioral/run.py --model <model-id> --case gate-clean --case gate-policy --case gate-stale --case gate-missing --case product-chain --output /tmp/new-gate-run
```

product-chain requests a separate Codex CLI reviewer through a fixed host capability using the selected model and consumes
additional model capacity. Its default timeout is 900 seconds, including the separate
reviewer; override it with --chain-timeout. Author and reviewer inputs must remain unchanged after the review.
Actual results and limits are in `reports/prd-gate-2026-10-04/README.md`.

The author sandbox cannot initialize a nested CLI app-server in this local host.
The evaluator therefore watches a fixed review-request.json action, then launches
one reviewer with its own workspace-write sandbox. It accepts no arbitrary command,
model override or external path. Host launch/result evidence stays outside the author
workspace; report content is generated only by the reviewer. Failure is recorded and
never replaced with an assembled or self-scored report.


The chain verifier requires host completion evidence, not the author-visible result
notification. The host reviewer runs in a separate protected workspace with a copy of
the author inputs and the runner's initial skill snapshot. Its event stream, completion
result and report SHA-256 values are retained outside the author workspace. Reports
are published only after a successful review; the runner compares their final bytes
against those host digests. No review request, a failed reviewer or replaced report
fails the chain even if author-visible events/result files claim success.

Chain author/reviewer invocations explicitly exclude `/tmp` and `$TMPDIR` from their
extra writable roots, so a temporary output directory does not grant the author write
access to the host evidence or reviewer workspace. This is a per-invocation setting,
not a change to the user's Codex configuration.
