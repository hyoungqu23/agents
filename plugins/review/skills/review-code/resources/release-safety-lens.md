# Release Safety Review Lens

This lens is triggered by the SHAPE of the change, not the stack. Apply it when the diff contains any of: database migration files, changes to an API contract consumed by a separately-deployed client (schema/DTO/endpoint changes), config/env-var changes, feature-flag changes, or data backfill scripts. Skip it for changes deployed atomically with all their consumers.

The question this lens answers: "can this change be deployed, half-deployed, and rolled back without breaking anyone?"

## MIGRATION-COMPAT — Schema Migration Backward Compatibility

Principle: during a rolling deploy, old code runs against the new schema (and sometimes new code against the old schema) — both must survive it.

Check:
- Destructive operations (drop/rename column or table, type narrowing, new NOT NULL without default) shipped in the same release as the code that stops using them — expand-contract (parallel change) is the safe pattern.
- Data backfills: idempotent, chunked for large tables, locking behavior on hot tables.
- Whether the migration can run while the previous app version is still serving traffic.

FAIL:
- A column/table still read or written by the currently-deployed code is dropped/renamed in this release.
- A new NOT NULL/constraint fails against existing rows or against writes from the still-running old version.
- A long-locking migration targets a hot table with no batching/online strategy.

WARN:
- Destructive cleanup is bundled with feature code instead of a separate later release — works if deploys are atomic, fragile otherwise.

## DEPLOY-ORDER — Cross-Service Deploy Ordering

Principle: when client and server (or two services) deploy independently, every intermediate combination of versions must work — or the required order must be explicit and enforced.

Check:
- New/changed API fields: does the old client tolerate the new response (and the new client the old response)? Are removed fields still sent until all consumers migrate?
- New endpoints consumed by a client released in the same cycle: which must go first? Is the order documented in the PR?
- Enum/status values added on the server: do already-deployed clients handle the unknown value (relates to EXHAUSTIVENESS in the common gate, but across the deploy boundary)?
- Cache/CDN: are stale bundles/responses valid against the new API during propagation?

FAIL:
- A realistic version combination during rollout (old client + new server, or new client + old server) breaks a user flow, and no deploy-order note exists.
- A server response field/status that deployed clients require is removed or renamed in one step.

WARN:
- Deploy order is required and known but only communicated verbally — recommend recording it in the PR/release notes.

## FLAG-GUARD — Risky Behavior Behind Flags

Principle: high-risk new behavior should be independently switchable from deploy; a deploy should not be the only off-switch.

Check:
- New risky paths (payments, bulk mutations, external integrations, irreversible data operations): toggleable? default off? kill-switch reachable without redeploy?
- Flag lifecycle: owner and removal plan for the flag; behavior when the flag service/config is unavailable (fail closed for risky paths).
- Both flag states actually tested — the off path must remain the previous behavior.

FAIL:
- The off state of the flag no longer preserves previous behavior (the "rollback" flag is a placebo).
- A risky irreversible operation ships enabled-by-default with no independent kill-switch, where the blast radius realistically justifies one.

WARN:
- Flag added without removal plan/owner, accreting permanent conditional complexity.

## ROLLBACK-READY — Revertability of the Release

Principle: assume this release will be rolled back at the worst moment; nothing should make that impossible.

Check:
- One-way data transforms (destructive normalization, irreversible encoding changes) without backup or reverse path.
- New writes that the previous version cannot read (serialization format, storage layout, queue message schema).
- Config/env changes: does the previous version still boot with the new config (and the new version with the old, for roll-forward)?

FAIL:
- After this release writes data for N minutes, rolling back to the previous version corrupts or cannot read that data, and no mitigation exists.
- Rollback requires a manual data repair that is undocumented.

WARN:
- Rollback works but silently loses feature data written in the interim — acceptable only if explicitly acknowledged.

## Evidence Requirements

- MIGRATION-COMPAT findings must cite the migration file and the code path still using the affected schema.
- DEPLOY-ORDER findings must name the concrete version pair that breaks (e.g. "deployed client X still reads field Y removed here").
- FLAG-GUARD / ROLLBACK-READY findings must cite the irreversible operation or untoggleable path, not hypothetical risk.
