# Review Lenses

Use this file when a review touches frontend behavior, framework conventions, tests, architecture, or broad maintainability.

## Shared Gates

Use `review-execution.md` for separate discovery passes, behavior tracing, scope control, and candidate handling. Apply `common-gate.md` for safety, all five quality criteria, and Change Restraint; this optional lens supplements those authorities. Test coverage and verification follow SPEC-COVERAGE there and Regression Sensitivity in `verification-matrix.md`.

Runtime Contract pass escalation:
- Use the pass when a finding depends on what an external or server-owned contract really is. Do not infer the contract only from a client type, mock, label, or generated assumption.
- Prefer primary sources in this order: server router/controller/schema, OpenAPI/GraphQL/protobuf/JSON schema, database migration/model, generated client source, official third-party docs, then tests/fixtures/mocks as supporting evidence.
- If the primary source is not already in context and the contract decides the finding, read that source directly when it is reachable; otherwise explicitly mark the candidate as excluded for insufficient contract evidence.

Include dead code, unused files, temporary preview routes, and local-only harness pages in the reviewed inventory.

## Frontend Stack Checks

Next.js App Router v15+:
- Check route segment conventions: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, and `route.ts`.
- Verify server/client boundaries. Files using state, effects, browser APIs, event handlers, or client-only hooks need `'use client'`; server components should not import client-only modules accidentally.
- Verify version-sensitive request APIs such as `params`, `searchParams`, `cookies()`, and `headers()` against the installed Next.js version before claiming a bug.
- Check route handlers for correct method exports, response typing, auth/tenant checks, cache behavior, and runtime compatibility.
- Check metadata, `next/image`, `next/font`, `next/script`, streaming/Suspense boundaries, and CSR bailout hooks such as `useSearchParams`.

React v19+:
- Enforce hook rules and dependency correctness; stale closures are findings only when a real path exists.
- Investigate derived state via `useState` + `useEffect` when it creates stale state or demonstrated unnecessary work. Require a concrete benefit before proposing render-time calculation or `useMemo`; the pattern alone is not a finding.
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

## Finding Promotion

Use the promotion conditions and dispositions in `review-execution.md#5-refute-and-dispose-candidates`, including the common gate's evidence and Change Restraint requirements. Stack-specific prompts above do not bypass that gate.
