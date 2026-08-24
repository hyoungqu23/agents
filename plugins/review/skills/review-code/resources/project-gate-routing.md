# Project Gate Routing

Use this file only when the repository, prompt, branch, path, or local instructions require a named project/product review gate.

## Source of Truth

Read and follow the project-specific review gate named by the repository's local instructions, docs, or prompt before applying this skill's generic severity labels.

If the gate points to additional criteria/resources, load the relevant files as needed. Do not redefine those criteria locally when the gate is available.

## Required Behavior

- Include staged, unstaged, and untracked files in review scope.
- Report only the finding levels required by the gate, with concrete file:line references.
- Apply all common criteria required by the gate. Apply frontend criteria to frontend code. Apply backend criteria only when backend code is in scope and the backend criteria exist.
- Treat temporary preview routes, local-only harness pages, debug pages, and accidental playground files as blockers unless the user explicitly says they are excluded from the commit.
- For convention findings, verify against the gate's convention resource before claiming a violation.
- For visual quality findings, read the gate's visual quality resource when UI behavior or layout changed and the change is not explicitly a small quick fix.
- If client behavior depends on a server contract, inspect the server schema/router/contract when reachable before claiming a client type or naming issue.

## Output Shape

Use the gate's required FAIL/WARN style when it exists:

```markdown
## 코드 리뷰 게이트 결과

[FAIL] <criterion>: path:line — 문제
  바꿀 것: 최소 수정 방향
  이유: 배포 차단 사유
  수정 후 상태: 기대 상태
  근거: 확인한 코드/문서/테스트

[WARN] <criterion>: path:line — 문제
  바꿀 것: 최소 수정 방향
  이유: 위험 또는 유지보수 비용
  수정 후 상태: 기대 상태
  근거: 확인한 코드/문서/테스트
```

If no gated findings remain after the evidence gate, say that no evidence-backed gated findings were found and list verification performed. Do not print PASS-by-category noise.
