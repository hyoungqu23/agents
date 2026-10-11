---
name: review-code
description: Completion-gated hard code review workflow for PRs, branches, diffs, and working-tree changes in any language or stack. Acquires available PR/spec context, inventories every changed and untracked file, routes matching project and stack specialists, discovers candidates broadly, promotes only evidence-backed findings, and verifies them with repository-native checks. Use when the user asks for code review, current changes review, PR review, pre-merge review, branch/diff review, project-specific review gate checks, strict file:line findings, or safe mechanical autofixes. For PR links or explicit PR-review requests, also recommends copy-ready inline review comments with exact file and diff-line placement. Do not use it to post those comments to a pull request, which is review-pr, or to answer a review on a pull request you authored, which is review-respond. For checking existing review claims without changes or posting, use review-check.
---

# Review Code

## Purpose and Default Quality Bar

Run a full-scope review of correctness, maintainability, repository fit, regression, and UI/UX. Keep the coverage ledger internal unless requested. Every invocation applies `resources/common-gate.md`, including all five engineering-quality criteria and Change Restraint. A concrete maintenance defect can be actionable even when tests pass; aim for the smallest complete fix and finish when the completion gate closes, without finding quotas or claims of perfection.

## Workflow

1. **Fix the target and intent.** Use the named PR, branch, commit range, or diff; otherwise include staged, unstaged, and untracked changes. For PRs, acquire title/body, base/head refs, commits, changed files, diff, and linked requirements through read-only host tools or CLI. For branch reviews, detect the base from a PR/MR, then `origin/HEAD`, `origin/main`, or `origin/master`. For other reviews, use the prompt, commit messages, and nearby issue/plan/docs evidence. Record inaccessible intent instead of inventing it. PR targets also receive inline comment recommendations unless opted out; recommendations do not authorize posting.
2. **Load authority and references before judgment.** Read repository instructions, conventions, manifests, tool configuration, and nearby maintained patterns. Detect stacks per changed area using package/framework manifests and file types, including mixed repositories. Follow `resources/skill-routing.md`; a named project gate and its report contract take precedence over conflicting generic guidance. Use installed-version or primary-source evidence for version-sensitive claims. Load the mandatory and applicable references below.
3. **Inventory and discover.** Follow `resources/review-execution.md` for the canonical file inventory, internal ledger, and separate Standards, Spec, and Runtime Contract passes. Use git status/diffs and untracked-file enumeration; reconcile PR file lists with the reviewed diff. Apply the common gate plus matching lenses to the complete inventory before suppressing candidates.
4. **Trace, refute, and dispose.** Use the execution harness's high-risk trace, promotion requirements, and candidate lifecycle. Read definitions, callers, consumers, tests, and safeguards needed to establish or refute each issue. For a deciding external/server contract, use the primary-source order in `resources/review-lenses.md`; keep inaccessible contracts unresolved. Preserve one finding per root cause. Quality findings require corroborating owners, dependencies, existing implementations, conventions, or callers. Apply Change Restraint to the proposed remedy; reading related code does not authorize unrelated cleanup.
5. **Verify and finish.** Choose and report repository-native checks with `resources/verification-matrix.md`, including Regression Sensitivity where applicable. Do not install dependencies, start required external services, or mutate external state without authorization. Re-diff any authorized autofixes, then close the execution harness's completion gate. Report exact scope and verification gaps under `## 검증`; a partial review must not imply complete coverage.

## PR Inline Comment Recommendations

For a PR URL/number or explicit PR review, recommend comments from promoted findings only:

1. Map each comment to one finding and the smallest valid changed head-side line (`RIGHT`, or platform equivalent). For an absence finding, anchor where the missing handling becomes actionable. If no valid diff anchor exists, keep the finding in the main report and mark it unsuitable for inline placement.
2. State the concrete trigger/effect or demonstrated structural cost and the smallest useful change. Keep one concern per comment, normally two to four short sentences. A question expresses a genuinely unresolved contract; it must not disguise a proven issue or uncertainty as a vague best-practice claim.
3. Follow the sole wording procedure in `resources/skill-routing.md#pr-comment-wording-route`: use `un-ai` from the `content` plugin, or its documented fallback. Keep severity and placement metadata outside the copy-ready quote. Recheck the final text against the evidence and diff anchor.

Never post comments or submit reviews without a separate user request.

## Autofix Boundary

Unless the user requested report-only review, autofix only mechanical, low-risk, locally obvious issues that pass Change Restraint. Safe cases include unused imports/locals, obvious new dead branches, stray debug logs, accidental local-only preview/harness pages, typo-level copy/comment fixes without meaning changes, and formatting required on changed code without unrelated churn.

Do not autofix API contracts, migrations, auth, persistence, caching, concurrency, test strategy, UX, broad refactors, ambiguous decisions, new abstractions, public behavior changes, or anything without an obvious minimal safe patch. Re-read the resulting diff and report every autofix; larger issues remain findings.

## Output Contract

Use the user's language. Lead with findings; omit praise and category-by-category PASS output. Local project gates can replace this report shape and severity vocabulary.

Severity:
- `P1`: blocker or high-risk correctness/security/data-loss/regression issue.
- `P2`: should fix before merge; meaningful maintainability, UX, test, or runtime risk.
- `P3`: non-blocking improvement with concrete value.

Apply the common gate's evidence and severity rules to quality findings; quality ambition alone cannot raise severity.

If autofixes were made, start with:

```markdown
## 자동 수정

- [AUTO-FIXED] path:line — 문제 -> 수행한 수정
```

For each finding, use this structure:

```markdown
## 리뷰 결과

### [P2] 제목 — path:line

- 문제: 구체적인 결함
- 바꿀 것: 최소 수정 방향
- 이유: 그대로 둘 때의 구체적 비용과 제안한 수정의 이익
- 수정 후 상태: 수정 뒤 보장할 상태
- 근거: 확인한 코드, 테스트, 문서, 명령
```

Use one `###` heading per finding, severity first and `— path:line` last; do not add horizontal rules or repeated blank-line separators. Each field is a top-level bullet. Put any multi-paragraph details or code blocks inside that field's bullet, separated by one blank line and indented to its content column. Excluded items and verification use compact one-line bullets.

For PR targets, place this section after findings and before excluded items/verification:

```markdown
## PR 코멘트 추천

### [P2] 제목 — path/to/file.ts:L42

> `result`가 비어 있으면 여기서 `result.items`를 읽다가 화면이 멈춥니다. 빈 응답을 먼저 처리하고 빈 상태를 보여 주세요.

### 인라인 코멘트로 추천하지 않음

- [P2] 다른 제목 — PR diff의 유효한 근거 라인이 없어 일반 본문에 유지
```

Use one `###` heading per recommended comment; the heading is placement metadata, not part of the quote. With no supported recommendations, keep the section and say `- 없음 — 인라인으로 남길 근거가 있는 발견 없음`. Omit it for non-PR targets unless requested.

If no findings remain, say that no evidence-backed blocking findings were found. Always finish with:

```markdown
## 검토했지만 제외한 항목

- <suppressed candidate or "없음"> — 제외 이유

## 검증

- 리뷰 범위: <target, file classification, coverage gaps>
- 요구사항 근거: <PR body, issue, prompt, docs or inaccessible source>
- 라우팅: <project gate, stack/lenses, specialists and missing fallback>
- 품질 기준: <five criteria and existing-implementation search evidence or review gaps>
- 실행: `<command>` — <outcome and relationship to the reviewed change>
- 잔여 위험: <unclosed paths or unperformed verification, or "없음">
```

## References

Read these for every review before discovery:
- `resources/common-gate.md`: engineering quality, Change Restraint, safety criteria, and severity evidence.
- `resources/review-execution.md`: scope, ledger, discovery passes, tracing, candidate lifecycle, and completion gate.
- `resources/verification-matrix.md`: repository-native checks, Regression Sensitivity, and result reporting.
- `resources/skill-routing.md`: authority precedence, specialist selection/fallback, and PR comment wording.

Read matching resources by stack or change shape:
- `resources/frontend-lens.md`: frontend web/component/UI changes; apply framework-specific rules only to that framework.
- `resources/backend-lens.md`: API/service/persistence changes through the detected backend's idioms.
- `resources/release-safety-lens.md`: migrations, independently deployed API contracts, config/env, feature flags, or backfills.
- `resources/review-lenses.md`: deeper framework, DTO/schema, TypeScript, test, architecture, or UI questions; also the primary-source order for unresolved contracts.
- `resources/project-gate-routing.md`: a named project/product gate required by local instructions, docs, or the prompt.

Other languages use the common gate and relevant behavior lenses through their own idioms; do not force frontend or framework criteria onto unrelated code.
