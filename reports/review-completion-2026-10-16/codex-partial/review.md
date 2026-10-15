## 리뷰 결과

### [P2] 비허용 역할에도 참으로 평가되는 문자열 반환 — permissions.py:2

- 문제: `return role == "admin" or "editor"`는 admin에는 `True`, 그 외 모든 입력에는 문자열 `"editor"`를 반환합니다. 따라서 editor에도 bool을 반환하지 않고, 다른 역할에는 False를 반환해야 한다는 계약을 위반합니다.
- 바꿀 것: base의 `return role in ("admin", "editor")`를 복원합니다.
- 이유: 일반적인 `if can_edit(role)` 호출에서는 비허용 역할도 허용으로 해석됩니다. `is True`로 검사하는 호출자는 editor까지 거부합니다. 이는 호출 방식별 영향 설명이며, 실제 운영 호출부는 이번 열람 범위에서 확인하지 못했습니다. 명시적 API 계약 위반 자체를 근거로 지적합니다.
- 수정 후 상태: admin/editor는 bool True, 그 외 역할은 bool False를 반환합니다.
- 근거: base AGENTS.md:1은 “can_edit returns bool and permits only admin/editor; any other role returns False”를 명시합니다. base permissions.py:2는 membership 검사로 이를 구현하며 head permissions.py:2에서 변경되었습니다. 입력이 유효 역할로 제한된다는 가정도 editor의 bool 계약 위반을 해소하지 못합니다. 새 추상화 없이 기존 표현 복원으로 해결됩니다.

## 검토했지만 제외한 항목

- 모든 입력에 문자열을 반환한다는 후보 — admin에서는 True로 단락 평가되므로 반박됨.
- editor의 참/거짓 평가가 False로 바뀐다는 후보 — 문자열은 truthy이므로 반박됨. 반환형 문제는 F1에 통합.
- 함수 이름 변경이나 별도 권한 계층 도입 — 현재 문제 해결에 필요하지 않아 제외.
- lookup.py, notes.md — 후보 판정 없이 사용자 요청으로 내용 검토를 연기했고 변경 목록에는 유지.

## 검증

- 완료 상태: 신뢰된 검사기의 최종 계산은 **partial**. permissions.py의 변경 hunk 정적 검토는 마쳤지만 전체 브랜치 리뷰는 미완료입니다. F1의 인용은 수용되었으며 최종 rejected_findings는 비어 있습니다.
- 리뷰 범위: base `ccdfbeaf1dd92a4ee32670f5e4d8d0c55d199bc1` → head `96557a7907adbec422acb8b7b0692253b524966f`. permissions.py는 source/high/reviewed, lookup.py는 source/medium/unreviewed, notes.md는 docs/low/unreviewed입니다. 미검토 파일의 위험도는 내용 검토 전 임시 분류입니다.
- 요구사항 근거: 사용자 요청, base AGENTS.md:1, base 구현, head 커밋 메시지 `simplify helpers`. 외부 PR/이슈는 조회하지 않았습니다.
- 라우팅: 지정한 trusted review-code 및 필수 공통 자료 사용. Python 함수의 권한 계약에 공통 기준과 backend AUTHZ 관점을 적용했으며 프레임워크나 실행 가능한 서버 경로는 확인되지 않았습니다. 전문 에이전트/추가 스킬은 사용하지 않았습니다.
- 품질 기준: 단일 권한 소유자라 응집성 문제 없음, 외부 import 없음, bool 계약과 predicate 이름 대조, base 규칙과 저장소 적합성 대조. permissions.py/AGENTS.md에서 `can_edit|admin|editor` 검색 및 트리 목록 확인. 두 파일을 열람하지 않아 전체 중복 구현 검색은 unresolved이며 세 검토 pass도 전체 범위 기준 partial입니다.
- 실행: `git -C /private/tmp/hm2-review-completion-codex-20261015/partial/source status --porcelain` — clean 확인. Git ls-tree, log, show, permissions.py 한정 diff와 제한된 grep으로 목록·계약·변경을 읽었습니다. lookup.py/notes.md의 내용은 열람하지 않았습니다.
- 실행: `python3 .eval-plugins/review/skills/review-code/scripts/review_result.py capture --worktree /private/tmp/hm2-review-completion-codex-20261015/partial/source --base ccdfbeaf1dd92a4ee32670f5e4d8d0c55d199bc1 --head 96557a7907adbec422acb8b7b0692253b524966f --output /private/tmp/hm2-review-completion-codex-20261015/partial/workspace/scope.json` — 성공, 세 변경 파일 포함.
- 실행: `python3 .eval-plugins/review/skills/review-code/scripts/review_result.py validate --worktree /private/tmp/hm2-review-completion-codex-20261015/partial/source --base ccdfbeaf1dd92a4ee32670f5e4d8d0c55d199bc1 --head 96557a7907adbec422acb8b7b0692253b524966f --result /private/tmp/hm2-review-completion-codex-20261015/partial/workspace/review-result.json --output /private/tmp/hm2-review-completion-codex-20261015/partial/workspace/assessment.json` — 종료 2, partial. 최초에는 필수 comment 누락이 발견되어 결과 JSON만 보완했으며 최초 판정은 assessment.initial.json에 보존했습니다.
- 미실행: 사용자 지시에 따라 대상 코드·테스트·lint/type/build와 base/head 실행 비교를 수행하지 않았습니다. 트리에 테스트 및 실행 도구 설정도 없으므로 테스트 assertion에 대한 회귀 민감도 추적은 할 수 없었습니다.
- 잔여 위험: 실제 소비자, 입력 제한, 추가 권한 검사 및 운영상 영향은 미확인입니다. 정적 반환값 추론을 런타임 재현으로 표시하지 않았습니다. 검사기는 대상·목록·인용 일관성을 확인할 뿐 추론의 정확성을 인증하지 않습니다.
- 변경 경계: source checkout 및 .eval-plugins 수정 없음. GitHub 쓰기, 네트워크, 설치 없음. 코디네이터 폴더에 결과물만 작성했습니다.
