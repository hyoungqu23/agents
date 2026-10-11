# Frontend Review Lens

Apply this lens when stack detection (SKILL.md Core Workflow step 3) finds a frontend web stack — e.g. `package.json` with React/Next.js/Vue/Svelte dependencies, or a diff dominated by component/UI code. Skip it entirely for backend-only or non-web changes. Local project gates override it.

Framework-specific checks below use Next.js/React vocabulary because that is the most common case; translate the principle to the detected framework when it differs.

Every FAIL/WARN below is a candidate, not an automatic verdict. Apply the evidence and Change Restraint gates in `common-gate.md` before reporting it. A code shape, stylistic difference, or missing reviewer verification is not by itself a defect. Keep optional improvements non-blocking and leave adequate code unchanged.

## CONVENTIONS — Repository Conventions and Architecture Fit

Principle: local conventions beat generic best practices.

Check:
- Local docs, `AGENTS.md`, package config, tsconfig aliases, lint/format config, folder ownership, naming, API client patterns, query hook patterns, form patterns, design-system usage, and nearby examples.

FAIL:
- The diff violates a documented repo convention in changed code.
- It introduces an implementation that conflicts with an explicit, applicable repository standard; cite the rule and the changed path.
- It commits temporary preview/debug/playground routes or local harness pages unless explicitly scoped out.

WARN:
- Divergence from a maintained local pattern causes a concrete maintenance or integration cost, and a small alignment has a clear benefit. Nearby usage alone does not establish a required convention.

## FRAMEWORK-API — Framework and Library API Correctness

Principle: review claims must match the installed framework/library versions.

Check:
- Next.js App Router file conventions, route handlers, server/client component boundaries, request APIs, caching, metadata, `next/image`, `next/font`, redirects, and middleware/proxy.
- React hook rules, effects, transitions, controlled inputs, hydration, list keys, and client-only APIs.
- Data libraries such as TanStack Query/SWR/Redux/RHF/Zod/MSW against installed major versions and repo patterns.

FAIL:
- Client-only hooks, state, effects, event handlers, or browser APIs are used across a server-only boundary.
- The installed API or router does not support the changed usage, causing a concrete failure or violating an explicit migration requirement.

WARN:
- A working older API conflicts with a documented migration direction and creates specific coordination or compatibility work. Deprecation alone does not justify a migration request.

## COMPONENT-FIT — Component Cohesion, Reuse, and Design-System Fit

Principle: components should be easy for the next developer to read, reuse, and modify without spreading domain logic across UI glue.

Check:
- Existing components/hooks/utilities, semantic duplication, prop shape, domain ownership, composition boundaries, direct design-system equivalents, and shared state placement.

FAIL:
- Existing common component/hook/API/schema pattern clearly covers the use case but the diff reimplements it incompatibly.
- Domain rules are duplicated in multiple UI components in a way that can diverge.

WARN:
- Related code has a demonstrated maintenance burden and a clear shared responsibility that a small change would simplify. If the shared contract or extraction boundary is unclear, do not recommend extraction solely because the code looks similar.

## RENDER-PERF — Rendering, Data Flow, and Performance

Principle: avoid render patterns that create stale UI, double rendering, layout churn, or expensive unnecessary work.

Check:
- Derived state via `useState` + `useEffect`, props-to-state synchronization, missing effect dependencies, stale closures, index keys with reordering/filtering, unstable object/array props, heavy calculations in render, large lists, Suspense/loading boundaries, hydration mismatch risk, and request waterfalls.

FAIL:
- `key={index}` is used for a dynamic list that can reorder/filter/insert/remove and a wrong item state can be reused.
- Props-to-state synchronization can overwrite user edits or display stale data on a realistic path.
- Rendering code can trigger request loops or hydration/runtime errors.

WARN:
- Repeated rendering, remounting, computation, or requests have a demonstrated cost at the expected input size or interaction frequency, and a bounded fix reduces that cost. Cite a measurement or concrete execution trace; do not invent a performance threshold.
- Missing memoization, an unstable reference, or an extra render alone is not a finding. Do not request memoization when it adds complexity without a demonstrated benefit.

## FAILURE-SEMANTICS — Defensive Code and Failure Semantics

Principle: defensive code should reveal uncertainty, not hide bugs as valid UI state.

Check:
- Redundant null checks after schemas, non-null assertions, unsafe casts, broad catch blocks, swallowed errors, default empty arrays/objects, toast/error handling, retry affordances, stale fallback UI, and typed success/failure modeling.

FAIL:
- Errors, parse failures, permission failures, or network failures are collapsed into empty/success UI.
- A fallback makes invalid data look valid or persists default data back to the server.

WARN:
- Redundant checks create a concrete clarity or maintenance problem, and local simplification preserves required failure handling. Before proposing removal, establish the guarantee from producers, schemas, callers, and async lifetimes; static types alone are insufficient.

## NAMING-CONSISTENCY — Naming, Type Shape, and Model Consistency

Principle: the same concept should have one name and one shape at each layer.

Check:
- API DTO versus domain/view model naming, snake_case/camelCase boundaries when relevant, file/component/hook names, boolean prefixes, event handler names, query keys, route names, and shared domain vocabulary.

FAIL:
- Inconsistent names misrepresent a contract and cause a concrete caller misunderstanding or violate an explicit domain naming rule. Intentional transport/domain names are not a defect.
- Transport fields leak into UI model code where the repo uses explicit mappers.
- A renamed field/status is not propagated through DTOs, transformers, consumers, and tests.

WARN:
- A local name obscures a specific distinction in meaning, units, or side effects, and a precise rename resolves it at low cost. Synonym preference is not a finding.

## UI-STATES-A11Y — Visual Quality and Accessibility Completeness

Principle: changed UI must be usable across states, input methods, and viewport constraints.

Check:
- Hover/focus/active/disabled/selected states, loading/empty/error/partial-data states, validation timing, submit loading/disabled behavior, keyboard access, focus management, accessible names, aria attributes, modal/dialog behavior, responsive text/layout, touch targets, scroll containment, transitions, and layout shift.

FAIL:
- New interactive controls lack keyboard access, accessible name, visible focus, or disabled behavior.
- Data UI lacks a realistic loading, empty, or error state.
- Modal/dialog changes break focus entry, escape/close behavior, or required aria semantics.
- Responsive layout can overlap, hide primary actions, or make content unusable.

WARN:
- An observed missing visual state creates a concrete feedback or usability problem while the control remains usable; do not request decorative transitions merely for completeness.
- Responsive polish issues are visible but not workflow-blocking.

## Evidence Requirements

- FRAMEWORK-API / RENDER-PERF / FAILURE-SEMANTICS findings need an actual runtime path, not only a grep match.
- If version-sensitive behavior has not been verified, record an unresolved evidence gap under verification rather than a FAIL against the code.
- NAMING-CONSISTENCY contract findings should cite at least two points when possible: DTO plus transformer, or API response plus UI assumption.
- CONVENTIONS findings should cite the local rule or nearby pattern.
- UI-STATES-A11Y findings should cite the changed UI element and the missing state/interaction.
