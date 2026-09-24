# Behavioral smoke runner

This runner executes real skills with `codex exec` rather than checking that a
fixture or prompt contains the expected words. It is a small regression gate, not
a score for overall skill quality or a replacement for the full scenario rubrics.

## Run

Use Codex CLI 0.153.4 (the CI-pinned version), with an existing Codex login or
`CODEX_API_KEY`. Model access is required. Each run consumes model capacity and
sends the copied skill instructions, references and synthetic task inputs to OpenAI.
No production repository or customer data is part of the fixtures.

```sh
python3 scripts/behavioral/run.py \
  --model <model-id> \
  --output /tmp/hm2-behavioral-unique-run
```

The output directory must not exist and must be outside this repository. Use
`--case design-existing` (repeatable) for a focused rerun and `--timeout 300` to
set the per-case limit. Each case runs once; a retry is a new evidence directory,
not a replacement for a failed attempt. The full suite must pass for a smoke pass.

The executor uses `workspace-write`, disabled web search, ephemeral sessions and
`--ignore-user-config`. It gets a copy of the plugin with its reference hierarchy,
plus raw inputs; `evals/`, setup instructions and grading expectations are excluded.
The skill is invoked by its explicit entrypoint, so this does not test automatic
skill discovery or marketplace loading. Local authentication remains in the CLI's
normal location. CLI-managed/global context may still differ from a clean CI host;
run on the clean hosted runner for release evidence.

## Cases and automated assertions

| Case | Source | What the grader checks |
| --- | --- | --- |
| `design-existing` | `design-brief` eval 1 | Only the app design source changes; original headings, rules and token values survive; CSS source and token names are mapped; decision log is added. |
| `content-fidelity` | Synthetic edit in `cases.py` | Original input and plugin files stay unchanged; requested intro is removed; dates/counts and explicit uncertainty/schedule caveats survive. |
| `review-runtime` | `review-code` eval 9 | A finding anchors `toInvoice.ts:9`, mentions the domain and label consumer, requests an archived-label fix, and reports no executed tests against the non-runnable fixture. |
| `review-check` | `review-check` eval 5 | Claim dispositions and ID coverage, historical fix status, missing evidence without severity, and report-only writes. |

The review task additionally asks for `review.json` to make the result inspectable.
It does not provide the expected defect, its location or the grading checklist.
Grading happens in the parent process after execution. A no-op, missing/malformed
output, unrequested edit, failed CLI invocation or timeout cannot pass.

These are deliberately narrow, deterministic assertions. A keyword match cannot
prove a correct explanation, and preserving numbers cannot prove that every claim
is faithful. Before release, a reviewer must inspect the full artifacts against the
skill's rubric for invented claims, contradictory rules, unsupported findings,
wrong meaning and scope omissions. Browser behavior, Claude behavior, all remaining
scenarios, and the `review-pr`/`review-respond` workflows are outside this smoke suite.

The `review-check` case uses eval 5: mixed claims, a fixed historical bug, missing
server evidence, conflicting policies, duplicate IDs, and a malicious reviewer
instruction. It checks report-only writes, dispositions, coverage, and recorded
checks. Runtime-test honesty is inspected in the qualitative pass. Read the actual evidence and explanations before accepting the result;
matching verdict labels alone does not establish sound reasoning.

## Evidence

Each case retains:

- `prompt.txt`, the exact task sent to the executor;
- `workspace/`, raw inputs, copied plugin and resulting artifacts;
- `before/`, the exact pre-execution inputs and skill source snapshot;
- `before.sha256.json` / `after.sha256.json`, input/source and final file hashes;
- `events.jsonl` and `stderr.log`, CLI trace and diagnostics;
- `result.json`, scenario origin, command, duration, status and every assertion.

`summary.json` records commit, dirty-tree state, CLI version, requested model,
reasoning effort, harness hashes and all case results. `full_suite` / `not_run`
distinguish a focused rerun from a full smoke run. The CLI trace provides usage
and any provider-reported model detail; an alias is not an immutable model version.
On an execution error the trace and workspace remain, even when final hashes cannot
be produced. Exit status is nonzero unless every selected case passes. Unit tests
use command doubles only to verify the runner's failure handling; they are never
reported as real behavioral executions.

## CI and release use

1. Store a scoped OpenAI credential as the repository secret `CODEX_API_KEY`.
2. Dispatch **behavioral-smoke** on reviewed `main` with an explicit model ID.
3. Download the artifact for that commit and run attempt; inspect checks and outputs.
4. Record the run URL and any remaining qualitative checks with the release.

The workflow fails if the secret is absent or the selected branch is not `main`.
It never uses `pull_request_target`, has read-only repository permissions, and does
not persist checkout credentials. Evidence is retained for 14 days; archive the
reviewed release evidence separately if it needs to live longer. GitHub branch
protection/publishing gates are external configuration and are not changed by this
repository patch. A missing or undispatched run is **not run**, never passed.

Execution follows the [official non-interactive Codex documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
