# Common Review Gate (stack-agnostic)

Apply this gate to every review regardless of detected stack, unless a stricter local project gate overrides it.

This gate is intentionally generic. Local `AGENTS.md`, framework versions, design-system docs, API specs, and repo conventions override it.

## Severity Policy

- `FAIL`: block or strongly recommend blocking merge until fixed. Use only when there is concrete file:line evidence and a realistic runtime, security, data, UX, or maintainability consequence.
- `WARN`: meaningful risk or maintainability cost that should be addressed or explicitly accepted.
- Do not emit PASS-by-category noise. If there are no findings, list verification performed and residual risk.
- Prefer the repo's own labels when a local gate exists.

## Engineering Quality — Required on Every Review

Apply all five criteria during the Standards pass, including changes whose behavior is correct and whose tests pass. Assess each changed behavior and its directly affected owners and consumers. For non-code files, record which criteria apply instead of inventing code-structure findings.

### COHESION — Responsibility and Ownership

- Identify the owning domain and reasons each changed module, function, component, or hook changes. Keep a domain rule with its owner and separate unrelated responsibilities when their combination creates a concrete cost.
- Look for business rules embedded in UI/transport glue, unrelated policies in a generic helper, or a single domain decision scattered across layers. Show which changes now require editing unrelated responsibilities or assembling one rule from multiple places.
- Recommend the smallest move or extraction into an existing owner when possible. A long file, multiple private helpers, or an orchestration function calling several services is not itself a defect. Do not require extra layers just to make code shorter.

### COUPLING — Dependencies and Change Propagation

- Trace imports and calls, shared state, argument/return shapes, and dependency direction. Check whether a consumer knows another module's internals, requires an unrelated runtime to use a domain rule, or must change for reasons outside its responsibility.
- Cite the dependency edge and affected consumer: cycles, cross-feature private imports, UI/framework dependencies in domain code, hidden global state, or broad objects passed where a stable narrow contract already exists.
- Prefer an existing public interface, a narrower contract, or moving the responsibility to its owner. A necessary dependency or a wrapper with no hidden decision does not justify dependency injection, a new interface, or another abstraction by itself.

### DUPLICATION — One Implementation per Owned Rule

- For every added or materially changed rule, search beyond the diff for the same domain operation, validation, transformation, calculation, state transition, query/key builder, or UI behavior. Read likely matches and their callers; text matching alone does not establish equivalence.
- Do not accept a second hand-maintained implementation of the same rule, even if the copies currently agree, tests pass, or only two copies exist. Cite both implementations, the shared invariant and inputs/outputs, and the sites that must be edited together. Reuse the canonical implementation or consolidate into the closest shared owner with a suitably narrow contract.
- Distinguish independently owned rules that happen to look alike. Separate policies with different change authority, independent expected values in tests, and generated artifacts with one generator are not parallel production implementations. Do not unify them solely because the syntax matches.
- When a real execution/deployment boundary prevents sharing executable code, verify an explicit repository contract and an existing generation or parity mechanism before accepting separate representations. Without that evidence, raise the concrete duplication/contract gap; do not demand an impossible cross-runtime import or accept an undocumented copy as a best practice.

### REPOSITORY-BP — Repository Patterns and Applicable Best Practices

- Establish the local authority: repository instructions, documented architecture/domain terms, public module interfaces, lint/type rules, and representative maintained implementations. Cite the source or counterpart for a claimed violation.
- Check reuse of established clients, helpers, hooks, schemas, errors, and test patterns before proposing another implementation. If competing patterns exist, check the documented migration direction and affected area; the most common or nearest legacy example is not automatically canonical.
- Apply language/framework best practices only when supported by the installed version, repository configuration, source, or authoritative primary documentation. Explain their concrete effect here; a slogan such as SOLID, DRY, clean code, or best practice is not evidence.
- Follow explicit local policy over generic preferences. Do not copy a proven defect merely for consistency; state the conflict and consequence. Propose a narrow, behavior-preserving improvement rather than an unrelated repository migration.

### NAMING — Meaning and Contract Accuracy

- Compare names to the domain concept, actual responsibility, inputs/outputs, units, lifecycle, and side effects. Inspect callers as well as definitions, including exported types, functions, parameters, fields, files, and test names touched by the change.
- Promote names that obscure a concrete distinction: milliseconds versus seconds, an ID versus a display value, a predicate versus a collection, a read-looking function that mutates state, or one domain concept named differently across an established boundary.
- State the exact replacement and why it better describes the contract. For public/schema/serialized identifiers, preserve compatibility with an internal rename or mapping, or identify the coordinated change required; do not casually rename an external contract.
- Do not flag every short name, demand synonyms, or enforce personal casing preferences unsupported by the repository. Brevity is acceptable when the local meaning is unambiguous.

### Quality Evidence and Severity

- A quality finding needs a changed `file:line` anchor, corroborating code or authority, a present structural cost or authoritative contract violation, and a smallest useful fix. A present cost includes maintaining one rule in multiple places or importing a UI runtime to reuse domain logic; no production incident is required.
- Treat demonstrated semantic duplication and material responsibility, dependency, convention, or naming defects as `P2` / `FAIL` when they should be fixed before merge. Bounded clarity improvements with a concrete benefit are `P3` / `WARN`. Reserve `P1` for separately proven high-risk effects.
- Try to refute findings with independent ownership, generated sources, compatibility constraints, documented migration/architecture exceptions, and actual callers. Record accepted exceptions with their evidence; do not silently skip a criterion.
- Report one root cause once even if it violates several criteria. A duplicated rule embedded in a UI module may violate cohesion, coupling, and duplication, but one owner/reuse fix should usually be one finding.

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
