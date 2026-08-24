# Common Review Gate (stack-agnostic)

Apply this gate to every review regardless of detected stack, unless a stricter local project gate overrides it.

This gate is intentionally generic. Local `AGENTS.md`, framework versions, design-system docs, API specs, and repo conventions override it.

## Severity Policy

- `FAIL`: block or strongly recommend blocking merge until fixed. Use only when there is concrete file:line evidence and a realistic runtime, security, data, UX, or maintainability consequence.
- `WARN`: meaningful risk or maintainability cost that should be addressed or explicitly accepted.
- Do not emit PASS-by-category noise. If there are no findings, list verification performed and residual risk.
- Prefer the repo's own labels when a local gate exists.

## INJECTION — Injection and Unsafe Execution

Principle: user-controlled or external data must not be directly inserted into SQL, shell commands, HTML, code execution, filesystem paths, redirects, or URL fetch targets.

Check:
- SQL/ORM raw queries, command execution, `eval`/`Function`, unsafe `innerHTML`, path construction, redirect targets, webhook callbacks, and server-side fetch URLs.
- Parameterization, allowlists, safe escaping/sanitization, and framework-specific safe APIs.

FAIL:
- User-controlled data reaches SQL/command/code/HTML/path/redirect/fetch sink without a safe boundary.
- Sanitization happens after the unsafe sink.

WARN:
- Dynamic construction is safe only because of implicit assumptions; ask for an allowlist or explicit validation if the path is non-obvious.

## TRUST-BOUNDARY — Trust Boundary and Runtime Contract Validation

Principle: external inputs are untrusted even when static types look correct.

Check:
- API responses, request bodies, form submissions, URL params/search params, env vars, local/session storage, webhooks, imported files, postMessage, feature flags, and AI/LLM output.
- Boundary parsing with the stack's schema-validation idiom (Zod, serde, pydantic, or equivalent) before render, persistence, command execution, or business decisions.
- Error paths from failed parsing or malformed data.

FAIL:
- Untrusted data is rendered, persisted, executed, or used for auth/permission decisions before validation.
- AI/LLM output drives HTML, SQL, shell, file paths, tool calls, or API requests without schema/allowlist validation.
- Parse failures are silently converted into valid-looking empty/default data that can hide production errors.

WARN:
- Validation exists but is broad enough to erase the safety claim, such as `any`, catch-all passthrough, or unchecked casts at the boundary.

## ASYNC-SAFETY — Async State, Concurrency, and Cache Safety

Principle: async flows and shared state must preserve user intent under races, retries, cancellation, and concurrent mutations.

Check:
- Request races, stale closures, effect/task cleanup, abort/cancel behavior, optimistic updates, cache/query invalidation, retry behavior, shared module state, read-check-write flows, locks/channels where the stack uses them, and concurrent form submits.

FAIL:
- A realistic race can show stale data as current, overwrite a newer user action, double-submit a mutation, lose data, leak another tenant/user's data, or corrupt shared state.
- A mutation succeeds but the changed queries/cache/state are not invalidated or updated, leaving consumers predictably stale.

WARN:
- Missing cleanup or cancellation can cause stale state or noisy errors but not data loss.
- Cache freshness assumptions are undocumented and easy to misread.

## EXHAUSTIVENESS — Variant, Status, and Exhaustiveness Completeness

Principle: added enum/status/union variants must be handled everywhere that branches on sibling values.

Check:
- Switches/match arms, status maps, renderers, reducers, cache-invalidation branches, permission gates, analytics/event mappers, route maps, icon/color maps, and error-state handlers.
- Exhaustiveness guards where the language supports them (`never`/`assertNever`/`satisfies Record<Union, ...>`, Rust `match` without `_` catch-all, etc.).

FAIL:
- New or changed variant lacks a handling branch in a runtime path.
- Default/else branch silently ignores an unhandled variant or displays a misleading state.

WARN:
- A default branch handles the value safely but hides the missing explicit case from future maintainers.

## SPEC-COVERAGE — Requirement and Test Coverage Mapping

Principle: changed behavior should be traceable to requirements and tests.

Check:
- User request, PRD, issue, PR body, acceptance criteria, previous behavior for refactors, and nearby test style.
- Unit/integration/e2e coverage for core behavior, edge cases, error paths, permissions, loading/empty/error states, and regressions.

FAIL:
- A clear requirement or regression-prone behavior changed with no meaningful test or explicit reason.
- Refactor claims behavior preservation but lacks coverage for the behavior being preserved and touches high-risk paths.

WARN:
- Tests exist but cover only happy path while the changed code adds meaningful edge/error/permission paths.

## Evidence Requirements

- INJECTION / TRUST-BOUNDARY / ASYNC-SAFETY findings need an actual runtime path, not only a grep match.
- EXHAUSTIVENESS contract findings should cite at least two points when possible: variant plus missing handler, source type/schema plus consumer.
- SPEC-COVERAGE findings should cite the requirement source and the uncovered behavior.

## Sources to Prefer When Verifying

- Local repo authority: `AGENTS.md`, conventions, package versions, lint/test config, nearby patterns, API schemas, generated clients, tests.
- Official/current docs for version-sensitive claims: framework docs, language docs, accessibility standards, security cheat sheets, and library docs.
