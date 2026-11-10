# Implement source gate — 2026-11-10

Actual related regression runs: existing 51 + new 22 = **73 passed**. These are
mechanical/evaluator regressions; they are not independent model/browser evaluation.
The new suite includes an actual Node assertion against wrongly implemented behavior;
all original AC IDs remain present, but the failed assertion prevents complete.

| Requested acceptance | Regression evidence |
| --- | --- |
| Original AC omitted from manifest | missing_or_ambiguous_ac; evaluator reads full original list |
| Active blocker omitted or deferred | open/deferred stay active; affected result must retain needs_decision and Q ID |
| Resolved/nonblocking questions | complete allowed with no active blockers |
| Explicit partial scope | source-backed exact scope citation succeeds; reason-only exclusion fails |
| Original changed | stale snapshots/reviews rejected, including source and question changes |
| Parser failure/check absent | unsupported format/version/missing companion/review remain gaps |
| IDs present but wrong behavior | semantic mismatch or failed actual Node behavior blocks completion |
| Direct input and standalone | all original 51 state/evaluator tests pass; parser bundled without Product dependency |

Cross-worktree check: implement directly consumed spec's Korean worked-example
original tables and extracted AC-list/AC-empty without catalog errors. Parser copies
are byte-identical. Current-target source evidence and behavioral checks remain
required; the helper cannot authenticate semantic judgment or actual tool execution.

Quick skill validation, Claude manifest and scratch installation/load checks passed.
The repository validate.sh cannot finish because the official local Codex plugin
validator is missing. No staging, commits or remote writes. plans/ was untouched.
See validation.json for the exact scope of these claims.

## Follow-up corrections — 2026-11-10

The hard-review counterexamples are fixed and covered by repository regressions.
The full Python suite now runs 355 tests successfully with
1 pre-existing optional design-note test skipped. Official
Codex/Claude validation and scratch plugin loading also pass. The official validator
was obtained at the exact CI-pinned upstream revision; its earlier absence no longer
blocks this verification. See [fix-validation.json](fix-validation.json).

The eight previously failing guard assertions now pass. Reports above describe the
original authoring run; no new independent model or live product evaluation is claimed.
