# Review Lenses

Use this file when a review touches frontend behavior, framework conventions, tests, architecture, or broad maintainability. It condenses the local review sources from the skill workspace and the portable parts of GStack `/review`.

## Source Synthesis

- GStack review: base-branch diff, scope drift, confidence calibration, pre-emit evidence gate, fix-first classification, and adversarial self-review.
- Generic review gate patterns: safety/completeness categories, frontend criteria, and FAIL/WARN discipline.
- Review history patterns: repo-convention priority, async lifecycle tracing, i18n/toast/query consistency, UI state completeness, and preserving prior behavior.
- Matt Pocock style: split Standards review from Spec review so a clean implementation of the wrong thing still gets caught.
- Caveman review: keep final comments short, actionable, and fix-directed.
- Code Review Excellence: prioritize defects, architecture, tests, security, performance, and maintainable feedback over taste.

## General Axes

Internal pass discipline:
- Run Standards, Spec, and Runtime Contract as separate investigation passes before ranking findings. Do not let a strong result on one pass suppress a failure on another pass.
- Standards pass asks whether the change fits the repo: documented conventions, local patterns, module boundaries, naming, folder ownership, framework idioms, maintainability, and test style.
- Spec pass asks whether the change does the requested thing: issue/PRD/PR body/user request coverage, behavior preservation for refactors, missing requirements, partial implementation, and scope creep.
- Runtime Contract pass asks whether the code that will actually run is safe and coherent: API/server/client DTO drift, runtime validation, schema parsing, nullability, enum/status variants, exhaustive handling, async/cache/state ordering, auth/tenant scoping, persistence, and error modeling.
- Merge the passes only after evidence collection. Final output stays finding-first; the pass labels are for analysis unless the user asks for the breakdown.

Spec and scope:
- Identify the intended behavior from the user request, PR body, issue, plan, TODOs, and commit messages.
- Flag scope creep when unrelated refactors/features expand blast radius.
- Flag missing requirements when the diff only partially implements the stated behavior.
- For refactors, verify old behavior is preserved unless the request explicitly changes it.

Standards and conventions:
- Prefer existing repo patterns over generic best practices.
- Check local naming, import boundaries, folder ownership, hooks/components/services layering, test shape, and domain vocabulary.
- Treat a one-off implementation as suspicious when the repo already has a helper, component, hook, API client, or schema pattern for the same concept.

Runtime correctness:
- Trace data from input to persistence/rendering. Look for nullability gaps, unchecked external data, stale cache, swallowed errors, contract drift, and silent data corruption.
- For new enum/status/type values, search all sibling usages and check exhaustive handling.
- For API/client/server boundaries, verify runtime validation occurs before untrusted data is used, not just that TypeScript types exist.
- For async flows, check request races, stale closures, cleanup, cancellation, optimistic updates, and concurrent mutation ordering.
- For security/trust boundaries, check SQL/command/template injection, XSS, unsafe HTML, path construction, auth/tenant scoping, and LLM output validation.

Runtime Contract pass escalation:
- Use the pass when a finding depends on what an external or server-owned contract really is. Do not infer the contract only from a client type, mock, label, or generated assumption.
- Prefer primary sources in this order: server router/controller/schema, OpenAPI/GraphQL/protobuf/JSON schema, database migration/model, generated client source, official third-party docs, then tests/fixtures/mocks as supporting evidence.
- If the primary source is not already in context and the contract decides the finding, use `contract-research` or explicitly mark the candidate as excluded for insufficient contract evidence.

Maintainability:
- Favor high cohesion and low coupling: domain logic should live near the owning domain, not leak through UI glue or shared utilities prematurely.
- Remove semantic duplication when two implementations must evolve together.
- Do not request abstraction just because code repeats; require a real shared concept, cross-call-site pressure, or meaningful complexity reduction.
- Flag dead code, unused files, temporary preview routes, and local-only harness pages in review scope.

Testing:
- Map tests to changed behavior and acceptance criteria when available.
- Prefer behavior tests over snapshots for business logic and UI workflows.
- Verify edge cases, error paths, permissions, loading/empty states, and regression paths, not just happy paths.
- For contract changes, look for schema/parser tests, DTO transformer tests, or exhaustive status/variant tests that would fail on drift.
- If tests are missing, name the specific behavior that should be covered and the likely test location or style.

## Frontend Stack Checks

Next.js App Router v15+:
- Check route segment conventions: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, and `route.ts`.
- Verify server/client boundaries. Files using state, effects, browser APIs, event handlers, or client-only hooks need `'use client'`; server components should not import client-only modules accidentally.
- Verify version-sensitive request APIs such as `params`, `searchParams`, `cookies()`, and `headers()` against the installed Next.js version before claiming a bug.
- Check route handlers for correct method exports, response typing, auth/tenant checks, cache behavior, and runtime compatibility.
- Check metadata, `next/image`, `next/font`, `next/script`, streaming/Suspense boundaries, and CSR bailout hooks such as `useSearchParams`.

React v19+:
- Enforce hook rules and dependency correctness; stale closures are findings only when a real path exists.
- Avoid derived state via `useState` + `useEffect` when render-time calculation or `useMemo` is enough.
- Check effect cleanup for subscriptions, timers, abortable requests, observers, and external listeners.
- Check list keys, controlled/uncontrolled inputs, memoization only where it prevents real churn, and transitions for expensive UI state changes.
- Watch for props-to-state synchronization that loses user edits or creates double-render regressions.

TypeScript v5+:
- Check boundary types first: API DTOs, form schemas, route params, environment variables, and external data.
- Prefer discriminated unions and exhaustive checks for statuses and variants.
- Flag `any`, unsafe casts, non-null assertions, and `unknown` bypasses when they hide a real unsafe path.
- Keep server DTO shapes and client model shapes explicit when the repo separates snake_case API data from camelCase UI models.
- Do not require strictness patterns that the repo cannot support unless the changed code creates a concrete risk.

TypeScript contracts and boundaries:
- API DTOs: identify the source of truth before judging names or dead types. For client/server work, compare the server response/schema, API client DTO, transformer, and UI model; flag only concrete drift such as a missing field, renamed status, wrong optionality, snake_case/camelCase leakage, or a cast that bypasses the transformer.
- Zod/schema boundaries: when the repo uses Zod or another schema library, untrusted inputs should be parsed at the boundary before use: route handler body/query params, API responses, form submissions, env vars, webhooks, localStorage/sessionStorage, URL search params, and LLM output. Flag validation that happens after data is already rendered/persisted, `z.any()`/broad passthrough that erases the safety claim, duplicated TS types that can drift from the schema, or `safeParse` failures that are silently converted to empty/default data.
- DTO to domain mapping: distinguish transport types from domain/view models. A good review traces `unknown/external -> schema parse -> DTO -> transformer -> domain/view model`. Flag direct `as SomeDto`, direct UI use of transport DTOs where the repo has model mappers, or mappers that drop required fields without tests.
- Discriminated unions: prefer a stable literal discriminant for mutually exclusive variants and workflow states. Flag boolean matrices, optional-field bags, or stringly typed status checks when the diff introduces variants that can become impossible states.
- Exhaustive checks: when a union/status/enum changes, search every switch, status map, renderer, query invalidation branch, reducer, permission gate, and analytics/event mapper that handles sibling values. Require an explicit case, an `assertNever`/`never` guard, or a `satisfies Record<Union, ...>` map where appropriate.
- Error modeling: prefer typed success/failure results at external boundaries when exceptions are intentionally converted into UI state. Flag catch blocks that collapse parse/network/permission errors into the same fallback and make the UI show stale or empty data as if it were valid.
- Evidence rule: a TypeScript contract finding needs at least two cited points in the path when possible, such as schema plus consumer, DTO plus transformer, new union member plus missing switch/map branch, or API response plus UI assumption.

UI/UX and accessibility:
- For new interactive elements, check hover/focus/disabled/selected states, keyboard access, accessible names, and focus management.
- For data views, check loading, empty, error, partial-data, and retry states.
- For forms, check validation timing, submit disabled/loading behavior, error placement, value preservation, and i18n.
- For responsive layouts, check text overflow, content overlap, touch target size, scroll containment, modal behavior, and layout shift.
- For destructive actions, check confirmation, undo/recovery, permission visibility, and success/error feedback.

## Finding Quality Gate

Promote a finding only when all are true:
- The issue is inside the review scope.
- There is file:line evidence.
- You can explain the user-visible, runtime, maintainability, or security consequence.
- You can give a concrete minimal fix direction.
- You tried to disprove it by reading nearby code, related call sites, and tests.

Suppress or move to excluded-items when:
- It is only style preference.
- It depends on missing product intent.
- It requires a speculative future refactor.
- The fix cannot be described concretely.
- The evidence is only a grep hit without reading the relevant code path.
