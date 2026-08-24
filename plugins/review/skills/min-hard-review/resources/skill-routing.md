# Supporting Skill Routing

Use this resource for every review. Supporting skills deepen a matching area; they do not replace full-scope inventory, the common gate, runtime tracing, or the completion gate.

## Routing Order

1. Read repository and user instructions first. A named local project gate is authoritative for its criterion codes, severity, required resources, and report shape.
2. Detect stacks and change shapes per affected area rather than assigning one stack to the whole repository.
3. Inspect the skills actually available in the current agent environment. Skill names can differ between Codex, Claude Code, and local installations; use an installed equivalent that clearly matches the described purpose.
4. Load only skills triggered by the diff. Do not load every possible specialist or claim a specialist was used when it was unavailable.
5. Apply installed-version and primary-source evidence when it conflicts with generic memory or an outdated recommendation.

## Route Table

| Trigger in the reviewed scope | Supporting skill to use when available | Built-in fallback |
| --- | --- | --- |
| Local instructions name a project/product review gate | The exact named local gate and its referenced resources | `project-gate-routing.md`, then common and matching built-in lenses; report the missing gate as residual risk |
| React components, hooks, rendering, state, or React performance | `vercel-react-best-practices`, `vercel:react-best-practices`, or an installed React review equivalent | Frontend lens plus repository patterns and installed React version |
| Next.js routing, server/client components, data fetching, caching, metadata, or framework APIs | `next-best-practices`, `vercel:nextjs`, or an installed Next.js equivalent | Frontend lens plus installed Next.js source/config and official version-matched docs |
| Vite-based React or another non-Next React bundler | React specialist only; do **not** route to Next.js-specific guidance | Frontend lens plus the detected bundler/configuration |
| Playwright tests or browser E2E behavior | `playwright-best-practices` or an installed Playwright equivalent | Tests lens plus repository Playwright config and existing test patterns |
| Accessibility semantics, keyboard flow, focus, contrast, or WCAG claims | `wcag-audit-patterns` or an installed accessibility audit equivalent | `UI-STATES-A11Y` with primary WCAG/platform evidence when a claim is promoted |
| Visual behavior where a runnable UI is available and visual verification is relevant | `visual-tester`, `design-review`, or a matching installed visual QA skill | Static UI-state review; record that live visual verification was not performed |
| PostgreSQL/Supabase schema, query, RLS, index, or migration behavior | `supabase-postgres-best-practices` or an installed Postgres specialist | Backend and release-safety lenses plus repository schema/migration evidence |
| Unresolved framework, API, standard, or external contract | `contract-research` | Keep the candidate unresolved and record the missing primary-source validation |
| PR inline comment wording | `dumbify`, then `anti-ai-writing` | Do not claim those transformations were applied; use the PR comment rules and report the missing wording pass if comments are still requested |

Backend framework skills are optional, not a whitelist. FastAPI, Django, Flask, NestJS, Express, Fastify, Rails, Spring, ASP.NET, Go HTTP stacks, Rust servers, and equivalent backends all receive the built-in backend and common lenses when their change shape matches. Load a framework specialist only if one is actually installed and relevant.

Likewise, frontend review is not limited to Next.js. React with Vite, Remix, Gatsby, Astro integrations, and other component-based web stacks receive the frontend lens. Apply a framework-specific skill only to code owned by that framework.

## Missing Specialist Fallback

An unavailable supporting skill does not automatically block the review. Continue as follows:

1. Apply the matching built-in lens and local repository conventions.
2. Use installed-version configuration, source, types, tests, and primary documentation that are already accessible.
3. Narrow claims to what this evidence proves. Leave unresolved contract questions out of promoted findings.
4. Add one verification line in this form:

```text
- 라우팅: <area> — 전문 스킬 `<name/purpose>` 미사용(설치되지 않음); <built-in lens/evidence>로 검토, <remaining limitation>은 잔여 위험
```

Do not produce one warning per missing skill. Consolidate by review area and mention only missing validation that materially limits confidence.

## Precedence and Conflicts

Use this precedence for directly conflicting guidance:

1. explicit user instruction
2. repository-local project gate and repository conventions
3. installed version, source, type definitions, and authoritative primary documentation
4. matching specialist skill
5. generic built-in lens

A higher source can override a specific recommendation, but it does not erase unrelated security, correctness, spec, or release-safety checks. Record meaningful conflicts and the evidence used to resolve them.

## PR Comment Wording Route

For every promoted finding selected for an inline comment:

1. Draft the concrete trigger, effect, and requested smallest change.
2. Apply `dumbify`: use plain words, short sentences, one concern, and concrete identifiers while preserving exact technical terms, API/type names, and code identifiers.
   - If the likely reviewer may not know a term, keep the term and explain what it does on first use: `race condition(동시 요청이 같은 상태를 읽고 쓰며 생기는 충돌)`. A short following clause is also valid when it reads better than parentheses.
   - Explain the mechanism, not merely a translated label. `race condition(경쟁 상태)` repeats the name without making the failure easier to understand.
   - After the first explanation, use the technical term alone. Do not annotate shared vocabulary or repeat the same parenthetical gloss throughout the comment.
   - Keep code identifiers exact and formatted as code, such as `cache`, `InvoiceStatus`, or `sync.RWMutex`; a plain explanation supplements them instead of replacing them.
3. Apply `anti-ai-writing`: remove filler, praise sandwiches, vague hedging, inflated significance, canned transitions, and unnecessary formatting without changing the technical claim. This pass may tighten the explanation but must preserve the exact term and enough plain-language context to understand the mechanism.
4. Recheck the comment against the finding evidence and exact diff anchor.

These wording skills change presentation only. They must never add a new finding, increase severity, invent a runtime effect, or turn an invalid line into a valid PR anchor.
