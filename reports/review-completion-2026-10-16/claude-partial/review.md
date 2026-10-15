## 리뷰 결과

### [P1] can_edit이 admin 외 모든 role에 편집 권한을 부여함 — permissions.py:2

- 문제: `return role == "admin" or "editor"`는 `role == "admin"`이 거짓이면 문자열 `"editor"`를 반환합니다. `or` 오른쪽이 `role == "editor"` 비교가 아니라 상수입니다.
- 바꿀 것: base처럼 `return role in ("admin", "editor")`로 되돌립니다. `role == "admin" or role == "editor"`도 같은 의미입니다.
- 이유: `"viewer"`, `"guest"`, 빈 문자열, `None`을 포함한 모든 non-admin role이 truthy 값을 받아 편집이 허용됩니다. 인가 우회입니다. 반환값도 bool이 아니라 문자열이 됩니다.
- 수정 후 상태: `can_edit`은 bool을 반환하고 admin/editor만 True, 그 외 role은 False입니다.
- 근거: head 2행 `    return role == "admin" or "editor"`, base 2행 `    return role in ("admin", "editor")`. `AGENTS.md:1`은 "can_edit returns bool and permits only admin/editor; any other role returns False ... Preserve both contracts."라고 명시합니다.

## 검토했지만 제외한 항목

- 저장소 안에 `can_edit` 호출자가 없으니 영향이 없다는 반박 후보 — 제외(disproved). `git grep`으로 호출자가 없음을 확인했지만 `AGENTS.md`가 보존해야 할 공개 계약으로 명시합니다. 계약 위반은 호출자와 무관하게 성립하고, 저장소 밖 소비자는 확인할 수 없습니다.
- 의도된 권한 정책 변경이라는 반박 후보 — 제외(disproved). 변경 근거나 계약 수정이 없고, 구현도 `or` 오른쪽이 상수여서 정책 표현으로 읽을 수 없습니다.

## 검증

- 리뷰 범위: base `8676ea2b…`, head `bc6d0ae3…`, 변경 3개 파일. `permissions.py`(source, high)만 검토했습니다. `lookup.py`(source, medium)와 `notes.md`(docs, low)는 요청에 따라 내용 검토를 미뤘고, 변경 목록에는 남겨 `unreviewed`로 기록했습니다. 두 파일의 diff 내용은 판단하지 않았습니다.
- 요구사항 근거: `AGENTS.md:1`의 API 계약(`can_edit`, `first_name`)과 사용자 프롬프트. PR 본문이나 이슈는 없습니다. `first_name` 계약은 `lookup.py` 검토 보류로 대조하지 않았습니다.
- 라우팅: 프로젝트 게이트 없음. 일반 gate와 backend/인가 관점으로 정적 검토했습니다. 전문 에이전트는 사용하지 않았습니다. PR 대상이 아니라 인라인 코멘트 추천은 생략했습니다.
- 품질 기준: 응집도, 결합도, 중복, 저장소 적합성, 네이밍을 `permissions.py`에 적용했습니다. `git grep`으로 `can_edit`과 `permissions`를 검색했고 다른 구현이나 호출자는 없습니다. `lookup.py`와 `notes.md`에는 적용하지 못했습니다.
- 실행: `review_result.py capture` — scope.json 생성, 파일 3개 확인. `review_result.py validate` — exit 2, status `partial`(`lookup.py`·`notes.md` 미검토, standards/spec/runtime pass partial), 적격 finding은 `can-edit-always-truthy`. 대상 저장소의 코드와 테스트는 실행하지 않았습니다(요청에 따라 금지, 저장소에 테스트도 없음).
- 잔여 위험: 검토는 **완료되지 않았습니다(partial)**. `lookup.py`와 `notes.md`의 결함 여부와 `first_name` 계약 준수는 미확인입니다. `can_edit`의 실제 소비자는 저장소 안에서 찾지 못했습니다. 동작은 실행이 아니라 Python `or` 의미론에 근거한 정적 판단입니다.
