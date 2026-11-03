# Implement forward evaluation

Use the repository's `scripts/behavioral/implementation.py` to prepare a new scratch
directory outside the repository with `prepare --case full|no-browser --output PATH`.
It copies only the installed skill instructions/helper (excluding evals), a synthetic
existing Node application, supplied inputs and a pre-existing user draft. It calls no
model and needs no packages or production data.

Give an independent execution host only `prompt.txt` and the prepared paths. Do not
supply grading code, expected observations or a suspected fix. Preserve raw host/tool
traces and its final answer outside the source checkout. Record actual host/model
identity, tool availability and execution limits. Use a new directory for retries.

For both cases, a separate observer must exercise the final actual app: status filters,
selection hidden/restored, empty versus error, retry/current filter, rapid filter
changes and wide/narrow layout. Record actual observed IDs/state/layout plus the
verified source digest outside the executor's inputs. Pass that observation file to
`grade --output PATH --observations FILE`. The grader checks those observations,
unchanged raw inputs/skill/user draft, a real source change, initial-baseline timing,
all three requirement IDs and its independently recomputed assessment.

For `no-browser`, invoke the same task on a host with browser execution explicitly
unavailable. A valid partial result with real useful code and an honest not_run
browser check is expected; service failures, missing output or fabricated completion
do not pass. The coordinator then observes the resulting app separately and runs
`grade --output PATH --observations FILE`; this does not upgrade the executor's
partial record or imply that it had browser access. Source changes alone are not
proof of useful implementation. Namespaced source anchors may preserve AC IDs;
omitted or unimplemented requirements still fail. Keep case.json as coordinator
evidence outside the executor's authorized write scope.

This helper does not execute generated code or authenticate observation truth.
Inspect the actual code and tool traces. The full run needs actual browser evidence,
not source-keyword grading or the executor's own summary. These two cases do not
establish all declared scenarios, automatic discovery, or both hosts' behavior.
