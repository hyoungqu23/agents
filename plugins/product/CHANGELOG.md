# Changelog

## 0.5.1 - 2026-11-12

- Keep the independently shipped SPEC readers byte-identical and exercise both against a shared accepted/rejected handoff corpus.

## 0.5.0

- Reject malformed canonical rows instead of omitting ACs/questions; keep frontmatter detection separate from examples and encoding failures.

- Add product:spec with bundled SPEC/QUESTIONS templates, source authority and readiness guidance, and a standalone handoff record checker.

## 0.4.0 — 2026-10-12

- Add flow-spec for traceable user actions, branches, open decisions and scoped flow updates.
- Preserve requirement and source links through the existing design handoff.
- Add actual-PRD, direct-entry, update, stale-review, untrusted-input and design-chain evaluations.

## 0.3.0 — 2026-10-04

- Enforce host proof of reviewer completion and report ownership in chain evaluation; isolate reviewer inputs/reports and reject copied or replaced results (2026-10-06).

- Add read-only prd-gate with verified findings, R1–R5 coverage, revision freshness and explicit readiness dispositions.
- Add clean, blocking-policy, stale-defect and missing-input cases plus a single-request chain with a separate reviewer invocation.

## 0.2.0 - 2026-10-04

- Add prd-write for traceable requirements and acceptance criteria, direct entry and scoped updates.
- Consume actual problem-frame artifacts while preserving source limits and open policies.

## 0.1.0 - 2026-10-04

- Add problem-frame for evidence-grounded product problem framing and scoped updates.
- Define shared artifact identities, provenance, assumptions, decisions and maturity.
- Add evaluation fixtures for observed/hypothetical problems, preserved constraints,
  contradictory solution proposals, embedded instructions and incremental updates.
