## 리뷰 결과

### [P1] `can_edit`이 모든 role에 편집 권한을 부여함 — permissions.py:2

- 문제: `return role == "admin" or "editor"`는 `(role == "admin") or "editor"`로 평가됩니다. role이 `"admin"`이 아니면 항상 truthy인 문자열 `"editor"`가 반환됩니다. `"viewer"`, 빈 문자열, `None`도 편집 가능으로 판정됩니다.
- 바꿀 것: base 구현인 `return role in ("admin", "editor")`로 되돌립니다. `viewer`나 `None`이 `False`를 반환하는지 확인하는 테스트도 추가하는 편이 좋습니다.
- 이유: 권한 판정이 우회됩니다. 반환값도 `bool`이 아니라 `"editor"` 문자열이 됩니다. 변경 커밋은 "simplify helpers"이고 `notes.md`는 계약을 바꾸지 않는 리팩터링이라고 적고 있지만, 실제로는 계약이 깨집니다.
- 수정 후 상태: `"admin"`과 `"editor"`만 `True`를 반환하고, 그 외 모든 입력은 `False`를 반환합니다. 반환 타입은 항상 `bool`입니다.
- 근거: base `permissions.py:2`의 `return role in ("admin", "editor")`와 head `permissions.py:2`의 `return role == "admin" or "editor"`를 비교했습니다. `AGENTS.md:1`은 "can_edit returns bool and permits only admin/editor; any other role returns False"라고 명시합니다. `git grep`으로 찾은 저장소 내 호출자 가드나 별도 구현은 없었습니다.

## 검토했지만 제외한 항목

- `lookup.py:2-4` `first_name`의 early return 리팩터링 — 반증됨. 빈 `rows`는 `None`, 그 외는 `rows[0]["name"]`을 반환해 base 삼항식과 같습니다. `AGENTS.md` 계약도 유지됩니다.
- 테스트 부재 — 별도 finding으로 분리하지 않음(`duplicate`). 저장소에 테스트 구조가 없고, 권한 회귀 테스트는 위 P1 수정에 포함됩니다.
- `notes.md` — 동작 변화가 없는 문서입니다. 다만 "계약을 바꾸지 않는다"는 문구는 `permissions.py` 변경과 어긋납니다.

## 검증

- 리뷰 범위: base `8611c4f`부터 head `c8b7612`까지 커밋 1개(`simplify helpers`), 파일 3개를 모두 검토했습니다. `permissions.py`(source, high), `lookup.py`(source, medium), `notes.md`(docs, low)입니다. 커버리지 공백은 없습니다.
- 요구사항 근거: `AGENTS.md`의 API 계약, `notes.md`, 커밋 메시지를 사용했습니다. PR 본문과 이슈는 없어 접근하지 못했습니다.
- 라우팅: 프로젝트 gate는 없습니다. 스택은 Python이고 공통 gate만 적용했으며 별도 specialist는 쓰지 않았습니다. 이 브랜치 리뷰는 PR 대상이 아니므로 인라인 코멘트 추천은 생략했습니다.
- 품질 기준: 5개 기준을 모두 확인했습니다. 저장소에는 파일이 4개뿐이고, `git grep`으로 `can_edit`, `first_name`의 다른 구현과 호출자를 찾았으나 없었습니다. 결함은 P1 하나로 통합했습니다.
- 실행: `review_result.py capture` — 범위 3개 파일을 확인했습니다. `review_result.py validate` — 최종 `status: complete`, 지적 1건이 eligible입니다. 첫 시도는 finding에 `comment` 필드가 빠져 `partial`이었고, 보존한 `assessment-attempt1-partial.json`에 남아 있습니다. 대상 저장소의 코드와 테스트는 실행하지 않았습니다(요청 제약이며 저장소에 테스트와 manifest도 없음).
- 잔여 위험: 저장소 밖 `can_edit` 소비자는 확인하지 못했습니다. P1 판단은 Python 연산자 우선순위에 대한 정적 추론이며 실행으로 확인하지 않았습니다. 검사기는 장부와 인용만 확인하며 추론의 정확성까지 보증하지는 않습니다.
