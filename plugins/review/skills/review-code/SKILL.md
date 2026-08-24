---
name: review-code
description: Completion-gated hard code review workflow for PRs, branches, diffs, and working-tree changes in any language or stack. Acquires available PR/spec context, inventories every changed and untracked file, routes matching project and stack specialists, discovers candidates broadly, promotes only evidence-backed findings, and verifies them with repository-native checks. Use when the user asks for code review, current changes review, PR review, pre-merge review, branch/diff review, project-specific review gate checks, strict file:line findings, or safe mechanical autofixes. For PR links or explicit PR-review requests, also recommends copy-ready inline review comments with exact file and diff-line placement.
---

# Review Code

## Overview

Run a strict, completion-gated review that catches correctness, maintainability, convention, regression, and UI/UX issues. Maintain an internal coverage ledger so evidence filtering cannot hide unreviewed files or code paths. Prefer small mechanical autofixes when they are obviously safe; report larger or semantic issues without touching code.

## Core Workflow

1. Establish the target and acquire authoritative intent before judging code.
   - If the user names a PR, branch, commit range, or diff, use that target. Otherwise review the current working tree, including staged, unstaged, and untracked files.
   - For a PR URL/number, use available read-only host tools, API, or CLI to collect the title, body, base/head refs, commits, changed-file list, reviewable diff, and linked issue or acceptance criteria. Treat those artifacts as specification evidence, not decoration.
   - For a working-tree or branch review, inspect the prompt, branch/commit messages, nearby docs, and issue/plan references. Detect a branch base from the PR/MR when available, then `origin/HEAD`, `origin/main`, or `origin/master`.
   - If authoritative intent cannot be accessed, do not invent it. Record the missing spec context and review behavior preservation, runtime safety, and repository fit from the evidence that is available.
   - Treat a PR URL/number or explicit PR-review request as a request for inline comment recommendations unless the user opts out. Recommending comments never authorizes posting them; submit comments or reviews only when the user separately asks.

2. Inventory the entire scope and start the internal coverage ledger described in `resources/review-execution.md`.
   - Use git-native context first: `git status --short`, `git diff --stat`, `git diff`, `git diff --cached`, and `git ls-files --others --exclude-standard`. For a PR, reconcile the host changed-file list with the locally available diff.
   - Add every changed file to the ledger, including staged, unstaged, untracked, generated, lock, test, config, migration, and documentation files. Classify files instead of silently dropping them.
   - Group related files into changed behaviors, then record risk, callers/consumers, external contracts, requirements, tests, candidates, and final disposition. Batch large diffs, but leave no file unclassified.

3. Detect project authority, stacks, and supporting specialists before forming findings.
   - Identify stacks per changed area from manifests and file types: `package.json` and declared frameworks, `Cargo.toml`, `pyproject.toml`/`requirements.txt`, `go.mod`, `Gemfile`, `build.gradle`/`pom.xml`, `*.csproj`, `tauri.conf.json`, and equivalent sources. Mixed repositories can require multiple routes.
   - Read local instructions and conventions such as `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, docs, package manifests, lint/test config, and nearby patterns.
   - If local instructions or the prompt require a project-specific review gate, read `resources/project-gate-routing.md` and apply it before the generic output contract.
   - Read `resources/skill-routing.md` and load only the specialists triggered by the detected change. If a matching specialist is unavailable, continue with the built-in lens and record the missing specialist validation and residual risk under `## 검증`.
   - For version-sensitive framework, language, accessibility, or test-framework claims, prefer installed-version evidence and official/current primary documentation over memory.

4. Discover candidates broadly in three independent passes before suppressing anything.
   - Standards pass: check repository conventions, documented patterns, framework idioms, ownership, naming, import boundaries, local domain style, and maintainability smells.
   - Spec pass: map each requirement from the prompt, issue, PR body, PRD, or plan to implementation and tests. For refactors, check behavior preservation unless a change is explicit. Record missing requirements, partial implementation, and scope creep as candidates.
   - Runtime Contract pass: trace code that can actually run. Check API/server/client DTO drift, runtime validation, parser boundaries, discriminated unions, exhaustive handling, nullability, async ordering, stale cache/state, auth/tenant scope, errors, persistence, and data-loss paths.
   - Read changed files with the surrounding definitions, callers, consumers, tests, and configuration needed to understand them. Candidate discovery optimizes recall; the evidence gate later controls precision.
   - Keep the pass notes and candidate registry internal unless the user asks for them.

5. Apply the common gate plus the built-in lenses matching the stack and change shape.
   - Always read `resources/common-gate.md` and apply its stack-agnostic criteria unless a stricter local project gate overrides a criterion.
   - For frontend web code, read `resources/frontend-lens.md`. This applies to React, Next.js, Vite-based React, and equivalent component/UI stacks; Next.js-only rules apply only when Next.js is actually present.
   - For backend server code, read `resources/backend-lens.md`. Apply its contract, authorization, persistence, validation, and failure criteria through the detected framework's idioms; it is not limited to FastAPI or NestJS.
   - For migrations, separately deployed API contracts, config/env changes, feature flags, or backfills, read `resources/release-safety-lens.md` regardless of language.
   - For Rust, Go, JVM, .NET, Ruby, and other stacks, apply the common gate plus maintainability and tests through that language's idioms. Do not force frontend or framework-specific criteria onto unrelated code.
   - If relevant, read `resources/review-lenses.md` for deeper architecture, boundary-type, schema, exhaustive-handling, UI/UX, test, and maintainability prompts.

6. Trace and refute every candidate before promotion.
   - Follow high-risk behavior from entry point or caller through transformation and trust boundaries to the render, persistence, network, process, or other observable effect. Use `resources/review-execution.md` for the trace and candidate lifecycle.
   - Every promoted finding needs a concrete `file:line` reference and the exact code path that makes it actionable. Absence findings still need an anchor where the missing handling, test, or documentation should be introduced.
   - State what to change, why it matters, and the expected post-fix state. Suppress speculation, preference-only notes, and issues with no concrete fix.
   - Try to disprove each candidate using nearby code, call sites, consumers, tests, feature flags, repository conventions, history when relevant, and the rest of the diff. Record each candidate as promoted, disproved, duplicate, out of scope, or unresolved.
   - If a contract question cannot be settled locally, route to `contract-research` when available. Otherwise keep it unresolved rather than upgrading uncertainty into a finding.

7. Verify with repository-native checks using `resources/verification-matrix.md`.
   - Inspect existing manifests, scripts, lockfiles, and tool configuration before choosing commands. Run the narrowest relevant test, type, lint, build, or static check first, then broaden when feasible.
   - Do not install dependencies, start network-dependent services, or mutate external state without authorization. Record exact commands and outcomes, including skipped, unavailable, blocked, pre-existing, and change-introduced failures.
   - A failing command becomes a finding only when the failure is attributable to the reviewed change and can be anchored to changed code. Otherwise report it as verification evidence or residual risk.

8. Pass the completion gate before writing the report.
   - Every PR, staged, unstaged, and untracked file is present and classified in the ledger.
   - Every high-risk changed behavior has its caller/consumer path and observable effect traced, or an explicit unresolved reason.
   - Every known requirement maps to implementation, test, or a promoted gap; every candidate has a final disposition.
   - Relevant verification ran, or each skipped check has a concrete reason and residual risk.
   - No file or high-risk path remains silently unreviewed. If the gate cannot close, state the exact review-scope or verification gap in `## 검증`; never imply a complete review.

## PR Inline Comment Recommendations

For a PR URL/number or an explicit PR-review request, add copy-ready comment recommendations to the final report. This section is a presentation layer over promoted findings, not a second source of findings.

1. Map each recommendation to exactly one evidence-backed finding. Do not turn suppressed candidates, preference-only notes, or praise into comments.
2. Anchor it to the smallest changed line that causes the problem, using the repository-relative path and the PR head/new-side line number (`RIGHT`, or the platform equivalent). For an absence finding, anchor the changed production line where the missing handling or test need becomes concrete.
3. Verify that the proposed line is part of the PR diff. If no valid inline anchor exists, do not invent one: keep the finding in the main report and list it as not suitable for an inline comment.
4. Make the comment stand on its own. Name the concrete failing condition and observable effect, then ask for the smallest useful change or verification. Keep one concern per comment and normally use two to four short sentences.
5. Match confidence to evidence. State proven behavior directly; ask a genuine question only when the contract is unresolved. Do not hide uncertainty behind vague wording such as “consider,” “might be better,” or “best practice.”
6. Before finalizing the comment text, load and apply `dumbify` and `anti-ai-writing` in that order:
   - `dumbify`: use plain words, one idea per sentence, and concrete identifiers and conditions. Preserve exact technical terms, API/type names, and code identifiers. When a technical term may be unfamiliar to the likely reviewer, pair its first occurrence with a short mechanism-based explanation in plain language, using parentheses or a short following clause. Use the technical term alone afterward. Do not replace it with a vague translation, explain vocabulary the reviewers already share, or repeat the same gloss.
   - `anti-ai-writing`: preserve accuracy first, including the exact technical term and any first-use explanation needed to understand it. Remove throat-clearing, praise sandwiches, significance inflation, hollow “not X but Y” reframes, generic review filler, em dashes, and over-formatting. Never invent a detail to make the comment sound more human.
7. Keep severity labels, gate codes, and report field names outside the quoted comment. The reviewer should be able to paste the quote into the PR without editing it.

## Autofix Boundary

Autofix only when the issue is mechanical, low-risk, and locally obvious, unless the user explicitly requested report-only review.

Safe autofix examples:
- unused imports, unused local variables, obvious dead branches introduced by the diff
- stray debug logs, temporary comments, accidentally committed local-only preview routes or harness pages when clearly not intended
- typo-level copy/comment fixes that do not alter product meaning
- one-file formatting nits only when they do not cause broad formatter churn

Do not autofix:
- API contract changes, data migrations, auth/permission behavior, persistence logic, caching semantics, concurrency fixes, test strategy, UX behavior, broad refactors, or ambiguous product decisions
- anything requiring a new abstraction or changing public behavior
- anything where the minimal safe patch is not obvious

After autofixes, re-read the changed diff and report what was changed. Larger issues remain findings only.

## Output Contract

Use the user's language. Be finding-first and avoid praise or PASS spam.

If autofixes were made:

```markdown
## 자동 수정
- [AUTO-FIXED] path:line — 문제 -> 수행한 수정
```

For findings:

```markdown
## 리뷰 결과

### [P1] 제목 — path:line

- 문제: 구체적으로 깨지는 지점
- 바꿀 것: 최소 수정 방향
- 이유: 버그/유지보수/UX/회귀 위험
- 수정 후 상태: 고쳐진 뒤 보장되어야 하는 상태
- 근거: 확인한 코드, 테스트, 문서, 명령

### [P2] 다음 발견 — path:line

- 문제: ...

### [P3] 그 다음 발견 — path:line

- 문제: ...
```

Separation rules, applied literally:
- **One `###` heading per finding**, severity tag first, `— path:line` last. The heading IS the separator: do not also add `---` rules or extra blank lines. A heading cannot collapse the way stacked blank lines can, and stacking both mechanisms just pads the report.
- Each field is its own top-level `-` bullet under the heading. Never use indented continuation lines without a `-`: they collapse into one rendered paragraph, which is the run-together output these rules exist to prevent.
- Multi-paragraph detail (repro steps, a code block) goes inside the relevant field's bullet, separated by a single blank line and indented to that bullet's content column.
- `## 검토했지만 제외한 항목` and `## 검증` keep tight one-line `-` bullets — no per-entry headings there.

Severity:
- `P1`: blocker or high-risk correctness/security/data-loss/regression issue.
- `P2`: should fix before merge; meaningful maintainability, UX, test, or runtime risk.
- `P3`: non-blocking improvement with clear value and concrete change.

For a PR target, place this section after `## 리뷰 결과` and before the excluded-items and verification sections. Omit it for non-PR reviews unless the user asks for PR-style comments.

```markdown
## PR 코멘트 추천

### [P2] 제목 — path/to/file.ts:L42

> `result`가 비어 있으면 여기서 `result.items`를 읽다가 화면이 멈춥니다. 빈 응답을 먼저 처리하고 빈 상태를 보여 주세요.

### 인라인 코멘트로 추천하지 않음

- [P2] 다른 제목 — 근거 라인이 PR diff에 없어 일반 리뷰 본문에만 유지
```

Use one `###` heading per recommended comment. The heading contains placement metadata; do not copy it into the PR comment. When there are no evidence-backed comments for a PR, keep the section and say `- 없음 — 인라인으로 남길 근거가 있는 발견 없음`.

If no main findings remain, say that no evidence-backed blocking findings were found, then list verification performed and residual risk. Always include:

```markdown
## 검토했지만 제외한 항목
- <suppressed candidate or "없음"> — 제외 이유

## 검증
- 리뷰 범위: <PR/commit/diff와 staged, unstaged, untracked 분류 결과>
- 요구사항 근거: <PR body, issue, prompt, docs 또는 접근 불가>
- 라우팅: <프로젝트 게이트, 감지한 스택/렌즈, 사용한 전문 스킬과 누락 fallback>
- 실행: `<command>` — <통과/실패/차단/미실행 및 변경과의 관계>
- 잔여 위험: <닫히지 않은 경로, 실행하지 못한 검증 또는 "없음">
```

Keep the full coverage ledger internal unless the user asks for it. The verification summary must still make review scope, specification evidence, specialist routing, command outcomes, and residual risk auditable.

## References

- Read `resources/common-gate.md` for every review — the stack-agnostic gate criteria and severity policy.
- Read `resources/review-execution.md` for every review — scope inventory, coverage ledger, discovery, runtime tracing, candidate disposition, and the completion gate.
- Read `resources/verification-matrix.md` for every review — how to choose and report repository-native test, type, lint, build, and static checks by stack.
- Read `resources/skill-routing.md` for every review — how to select project and stack specialists and how to continue when one is unavailable.
- Read `resources/frontend-lens.md` when stack detection finds a frontend web stack, or when the diff touches component/UI code.
- Read `resources/backend-lens.md` when stack detection finds a backend server stack (FastAPI/Django/Flask, NestJS/Express/Fastify, or equivalent) or the diff touches API/service/persistence code.
- Read `resources/release-safety-lens.md` when the diff contains DB migrations, API contract changes consumed by separately-deployed clients, config/env changes, feature flags, or data backfills — triggered by change shape, not stack.
- Read `resources/review-lenses.md` when the diff touches frontend architecture, Next.js App Router, React hooks/rendering, TypeScript boundary types, API DTOs, Zod/schema validation, discriminated unions, exhaustive checks, UI/UX, tests, or maintainability.
- Read `resources/project-gate-routing.md` only when local instructions, repo docs, or the prompt require a named project/product review gate. Project gates define their own criterion codes; use the gate's vocabulary when routed there.
