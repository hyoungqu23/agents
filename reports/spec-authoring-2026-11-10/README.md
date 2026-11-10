# Spec authoring checks — 2026-11-10

SPEC/QUESTIONS are a small self-authored worked example from adjacent direct inputs.
The helper accepts its Korean canonical tables and opaque AC IDs. Structural
acceptance is not independent semantic validation or implementation/runtime QA.
Twelve mechanical regressions cover unsupported formats, missing review rows,
active deferred questions, nonblockers/resolved questions, drift and symlinks.
The 27 behavioral scenarios are definitions and have not been executed as model
runs. Image-input and independent-reader/other-host behavior remain untested.

## Follow-up corrections — 2026-11-10

The hard-review counterexamples are fixed and covered by repository regressions.
The full Python suite now runs 344 tests successfully with
1 pre-existing optional design-note test skipped. Official
Codex/Claude validation and scratch plugin loading also pass. The official validator
was obtained at the exact CI-pinned upstream revision; its earlier absence no longer
blocks this verification. See [fix-validation.json](fix-validation.json).

The eight previously failing guard assertions now pass. Reports above describe the
original authoring run; no new independent model or live product evaluation is claimed.
