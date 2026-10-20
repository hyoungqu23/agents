## 리뷰 결과

### [P3] can_edit가 해시 불가능한 role에서 False 대신 TypeError를 낸다 — permissions.py:2

- 문제: 튜플 `("admin", "editor")` 멤버십을 set 리터럴 `{"admin", "editor"}`로 바꿨다. set 멤버십은 피연산자를 해시하므로 list/dict 같은 해시 불가능한 `role`이 들어오면 `TypeError`가 난다. 기존 튜플은 `==` 비교라 `False`를 반환했다.
- 바꿀 것: 튜플로 되돌린다. 값이 두 개뿐이라 set으로 얻는 이점이 없다.
- 이유: `AGENTS.md`는 "can_edit returns bool and permits only admin/editor; any other role returns False. Preserve both contracts."라고 정의하고, `notes.md`와 커밋 메시지(`simplify helpers`)도 동작 보존 리팩터링이라고 밝힌다. 이 변경은 스타일만 바꾸면서 "그 외 role은 False"라는 계약을 일부 입력에서 깨뜨린다. 권한 검사에서 예외는 거부가 아니라 호출 실패로 번진다.
- 수정 후 상태: role 값의 타입과 무관하게 `admin`/`editor`만 `True`, 나머지는 모두 `False`.
- 근거: base `permissions.py:2`는 `return role in ("admin", "editor")`, head는 `return role in {"admin", "editor"}`다. `git grep`으로 base에서 `can_edit`/`first_name`을 찾으면 정의와 `AGENTS.md`뿐이라 호출부가 없다. 그래서 실제 role 타입(문자열일 가능성이 높다)은 확인하지 못했고, 이 때문에 P3로 둔다.

## 검토했지만 제외한 항목

- `lookup.py` `first_name` 가드 재작성 — `if not rows`는 기존 `if rows`의 정확한 부정이라 모든 입력에서 결과가 같다(빈 값 → `None`, 그 외 → `rows[0]["name"]`). 계약 유지, 반박됨.
- `notes.md` 신규 한 줄 — 동작 영향 없는 문서라 변경할 가치가 없다. 내용은 `AGENTS.md`와 일치한다.

## 검증

- 리뷰 범위: `ed503157..e73cce15` 단일 커밋, 3개 파일(`lookup.py` M, `notes.md` A, `permissions.py` M). `scope.json`의 파일 목록과 전부 대조했고 누락은 없다.
- 요구사항 근거: `AGENTS.md`의 API 계약, `notes.md`, 커밋 메시지. PR 본문과 이슈는 없다(브랜치 diff 대상).
- 라우팅: 프로젝트 게이트 없음. Python 소스 2개, 문서 1개라 backend/frontend/release-safety 렌즈는 해당 없음. 전문 에이전트는 쓰지 않았다.
- 품질 기준: 응집도·중복·저장소 적합성·네이밍은 확인했다. 결합도는 호출부가 없어 해당 없음. 저장소에 파일이 4개뿐이라 `git grep`으로 기존 구현을 찾았고 중복 구현은 없었다.
- 실행: `review_result.py capture` — 3개 파일 범위 확정. `review_result.py validate` — `complete`, `gaps: []`, eligible finding 1건(`can-edit-unhashable-role`). 이 검사는 장부와 인용 일치만 확인하며 추론의 정확성은 보증하지 않는다. 대상 저장소의 코드와 테스트는 실행하지 않았다(요청 사항, 저장소에 테스트도 없음). 그 외 파일 쓰기는 coordinator 폴더에만 했다.
- 잔여 위험: (1) 호출부가 없어 `can_edit`에 해시 불가능한 role이 실제로 들어오는지는 불명이다. (2) `TypeError`는 Python 의미론에서 도출했을 뿐 런타임으로 재현하지 않았다. (3) 첫 시도에서 `review-result.json`을 heredoc으로 쓰려던 Bash 호출이 자동 거부되어 Write 도구로 다시 작성했다. 최종 파일은 검증기를 통과했다.
