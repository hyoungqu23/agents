# Review harness evaluation — 2026-11-06

Actual model runs used the installed Codex CLI 0.156.1, its default `gpt-6-astra`,
and the tool-disabled read-only adapter. Inputs are synthetic repositories and
review claims; no target program, live GitHub review write or launchd installation
was executed. These runs do not establish broad defect detection or false-positive
rates. The individual packets, targets, responses and assessments are retained here;
`summary.json` records their hashes. Temporary paths/SHAs identify disposable fixtures.

| Scenario | Observed behavior | Computed scope result |
| --- | --- | --- |
| S1 | Found the removed empty-input guard; recorded caller/spec/runtime limitations instead of claiming executed tests | partial, supported finding eligible |
| S2 | Kept the unimplemented fix as a proposal with no completion reply; answered the ordering question using 질문 without severity | complete claim envelope |
| S3 | Found the empty-input regression against the supplied PR requirement | complete recorded static scope |
| S4 | Kept the original empty-input finding historically valid but now addressed; separately found reversed export ordering | complete recorded static scope and claim envelope |

`complete` is the structured checker's accounting result, not proof that every
defect was found or that runtime behavior was executed. S1's partial result is an
expected honest limitation, not a passing runtime test. The exact outputs are
model-generated; the grader did not edit them to make them pass.

Reproduce with the opt-in `tools/review-harness/tests/model_smoke.py` runner. It
uses real model capacity and is deliberately excluded from automatic unittest/CI
collection. The S1 run was made before that runner was extracted; S2–S4 used it.
Subsequent queue/delivery fixes are covered by deterministic regression tests;
these model runs should not be represented as new executions on every later commit.

Independent forward use also exercised S2/S4 skills and the real implement
assessment/notification path through a harmless harness stub. It found and led to
fixes for question severity, null-reply state consistency, relative input-source
paths, missing S4 review bodies and published-finding deduplication. No synthetic
target program or remote write was involved in those probes.

Additional checks include actual Git snapshots preserving staged/unstaged/untracked
content, SQLite restart recovery, reply-response loss, protected manual drafts,
same-head conversation changes, own-submission loop prevention, real wheel/sdist
builds and an offline install outside the development checkout/skill caches.
Homebrew clean-Mac installation is a CI check. Claude's real model adapter, actual
GitHub Pending visibility/replies and launchd login lifecycle remain unverified;
the package is not a published release or an installed background service yet.
