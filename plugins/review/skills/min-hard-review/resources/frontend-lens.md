# Frontend Review Lens

Apply this lens when stack detection (SKILL.md Core Workflow step 2) finds a frontend web stack — e.g. `package.json` with React/Next.js/Vue/Svelte dependencies, or a diff dominated by component/UI code. Skip it entirely for backend-only or non-web changes. Local project gates override it.

Framework-specific checks below use Next.js/React vocabulary because that is the most common case; translate the principle to the detected framework when it differs.

## CONVENTIONS — Repository Conventions and Architecture Fit

Principle: local conventions beat generic best practices.

Check:
- Local docs, `AGENTS.md`, package config, tsconfig aliases, lint/format config, folder ownership, naming, API client patterns, query hook patterns, form patterns, design-system usage, and nearby examples.

FAIL:
- The diff violates a documented repo convention in changed code.
- It introduces a second implementation style for an already-standardized pattern.
- It commits temporary preview/debug/playground routes or local harness pages unless explicitly scoped out.

WARN:
- The repo has a strong nearby pattern but no documented rule; recommend aligning unless there is a clear reason.

## FRAMEWORK-API — Framework and Library API Correctness

Principle: review claims must match the installed framework/library versions.

Check:
- Next.js App Router file conventions, route handlers, server/client component boundaries, request APIs, caching, metadata, `next/image`, `next/font`, redirects, and middleware/proxy.
- React hook rules, effects, transitions, controlled inputs, hydration, list keys, and client-only APIs.
- Data libraries such as TanStack Query/SWR/Redux/RHF/Zod/MSW against installed major versions and repo patterns.

FAIL:
- Client-only hooks, state, effects, event handlers, or browser APIs are used across a server-only boundary.
- Deprecated or wrong-router APIs are introduced in code that should use the current app architecture.
- A framework API claim is made without checking the installed version when the behavior is version-sensitive.

WARN:
- Older API still works but conflicts with the repo's migrated pattern or creates avoidable migration debt.

## COMPONENT-FIT — Component Cohesion, Reuse, and Design-System Fit

Principle: components should be easy for the next developer to read, reuse, and modify without spreading domain logic across UI glue.

Check:
- Existing components/hooks/utilities, semantic duplication, prop shape, domain ownership, composition boundaries, direct design-system equivalents, and shared state placement.

FAIL:
- Existing common component/hook/API/schema pattern clearly covers the use case but the diff reimplements it incompatibly.
- Domain rules are duplicated in multiple UI components in a way that can diverge.

WARN:
- Similar JSX/hook/API patterns repeat enough that extraction should be considered, but the abstraction boundary is not yet obvious.

## RENDER-PERF — Rendering, Data Flow, and Performance

Principle: avoid render patterns that create stale UI, double rendering, layout churn, or expensive unnecessary work.

Check:
- Derived state via `useState` + `useEffect`, props-to-state synchronization, missing effect dependencies, stale closures, index keys with reordering/filtering, unstable object/array props, heavy calculations in render, large lists, Suspense/loading boundaries, hydration mismatch risk, and request waterfalls.

FAIL:
- `key={index}` is used for a dynamic list that can reorder/filter/insert/remove and a wrong item state can be reused.
- Props-to-state synchronization can overwrite user edits or display stale data on a realistic path.
- Rendering code can trigger request loops or hydration/runtime errors.

WARN:
- Derived state or unstable props cause avoidable extra renders without a clear runtime bug.
- Heavy computation lacks memoization in a hot path with realistic scale.

## FAILURE-SEMANTICS — Defensive Code and Failure Semantics

Principle: defensive code should reveal uncertainty, not hide bugs as valid UI state.

Check:
- Redundant null checks after schemas, non-null assertions, unsafe casts, broad catch blocks, swallowed errors, default empty arrays/objects, toast/error handling, retry affordances, stale fallback UI, and typed success/failure modeling.

FAIL:
- Errors, parse failures, permission failures, or network failures are collapsed into empty/success UI.
- A fallback makes invalid data look valid or persists default data back to the server.

WARN:
- Defensive checks are noisy or inconsistent but do not hide a real failure path.

## NAMING-CONSISTENCY — Naming, Type Shape, and Model Consistency

Principle: the same concept should have one name and one shape at each layer.

Check:
- API DTO versus domain/view model naming, snake_case/camelCase boundaries when relevant, file/component/hook names, boolean prefixes, event handler names, query keys, route names, and shared domain vocabulary.

FAIL:
- The same domain concept is introduced under multiple names in changed code.
- Transport fields leak into UI model code where the repo uses explicit mappers.
- A renamed field/status is not propagated through DTOs, transformers, consumers, and tests.

WARN:
- Naming drift is local and non-breaking but likely to confuse future changes.

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
- Visual states or transitions are incomplete but the control remains usable.
- Responsive polish issues are visible but not workflow-blocking.

## Evidence Requirements

- FRAMEWORK-API / RENDER-PERF / FAILURE-SEMANTICS findings need an actual runtime path, not only a grep match.
- NAMING-CONSISTENCY contract findings should cite at least two points when possible: DTO plus transformer, or API response plus UI assumption.
- CONVENTIONS findings should cite the local rule or nearby pattern.
- UI-STATES-A11Y findings should cite the changed UI element and the missing state/interaction.
