## 리뷰 결과

### [P2] 비허용 역할의 False 반환 계약을 유지해야 함 — permissions.py:2

- 문제: `can_edit([])` 또는 `can_edit({})`처럼 해시할 수 없는 역할을 전달하면 새 집합 membership에서 `TypeError`가 발생합니다. base의 튜플 membership은 이 입력에 `False`를 반환합니다.
- 바꿀 것: 기존 `role in ("admin", "editor")`를 복원합니다.
- 이유: base `AGENTS.md:1`은 `can_edit`가 bool을 반환하고 admin/editor 이외의 모든 역할에는 `False`를 반환하도록 명시합니다. 함수에는 문자열 전용 타입 제한이나 검증 가드가 없습니다. 기존 연산 복원만으로 추가 입력 제약 없이 계약을 유지할 수 있습니다.
- 수정 후 상태: admin/editor는 `True`, 리스트·딕셔너리를 포함한 비허용 역할은 기존 계약대로 `False`를 반환합니다.
- 근거: base/head `permissions.py:2`, base `AGENTS.md:1`, head `notes.md:1`. 전체 저장소에서 호출자와 검증 계층을 검색했으나 두 함수 정의 및 계약 외 소비자는 없었습니다. 따라서 실제 서비스 장애나 권한 우회를 주장하지 않으며, 공개 함수 진입점과 명시된 계약에 한정한 회귀입니다. 결과는 정적 분석이며 실행 재현이 아닙니다.

## 검토했지만 제외한 항목

- 빈 목록 조회 오류 — `lookup.py:2-3`에서 인덱싱 전에 `None`을 반환하므로 base와 동일합니다.
- 정상 문자열 역할의 허용/거부 변화 — admin/editor, guest 및 `None`의 결과는 유지됩니다. 이 반례는 비해시 가능 입력의 계약 위반을 해소하지 않습니다.
- 첫 행의 name 누락 — `KeyError`는 base에도 존재하므로 이번 변경의 회귀가 아닙니다.

## 검증

- 완료 상태: 신뢰된 검사기의 최종 계산은 **complete**입니다. 변경된 3개 파일의 정적 범위와 증거 인용 검증이 완료되었다는 뜻이며, 런타임 검증이나 무결함 보장은 아닙니다.
- 리뷰 범위: `f817b95a50b23c1d9fd4fe4585c59208e58fecbd..754961f7b370151d79ba0bc726c88dbbc7045f26`; source 2개(`lookup.py`, `permissions.py`), docs 1개(`notes.md`). 누락 파일 없음.
- 요구사항 근거: base `AGENTS.md`, head `notes.md`, 커밋 메시지 `simplify helpers`. 계약 보존 의도를 기준으로 비교했습니다.
- 라우팅: 지정된 `.eval-plugins/review/skills/review-code/SKILL.md`와 필수 공통/실행/검증/라우팅/결과 계약 적용. Python 함수이며 서버 프레임워크는 없습니다. backend lens를 읽되 HTTP/DB/서비스 경로에 관한 기준은 적용하지 않았습니다. 추가 전문 에이전트나 네트워크 검증은 사용하지 않았습니다.
- 품질 기준: 응집도는 함수별 단일 책임, 결합도는 외부 의존 없음, 중복은 전체 트리 및 함수/인수 검색으로 별도 구현 없음, 저장소 적합성은 base 계약, 명명은 함수의 실제 책임과 대조했습니다. 문서는 의도에 부합하며 코드 구조 기준은 해당하지 않습니다.
- 실행: `git -C /private/tmp/hm2-review-completion-codex-20261015/clean/source diff f817b95a50b23c1d9fd4fe4585c59208e58fecbd 754961f7b370151d79ba0bc726c88dbbc7045f26` — 전체 변경 검토.
- 실행: `git -C /private/tmp/hm2-review-completion-codex-20261015/clean/source ls-tree -r --name-only 754961f7b370151d79ba0bc726c88dbbc7045f26` 및 `git -C /private/tmp/hm2-review-completion-codex-20261015/clean/source grep -n -e can_edit -e first_name -e role -e rows 754961f7b370151d79ba0bc726c88dbbc7045f26` — 전체 4파일에서 정의/계약 확인, 호출자·테스트·검증 구성 없음.
- 실행: `git -C /private/tmp/hm2-review-completion-codex-20261015/clean/source status --porcelain` — clean 확인.
- 실행: `python3 .eval-plugins/review/skills/review-code/scripts/review_result.py capture --worktree /private/tmp/hm2-review-completion-codex-20261015/clean/source --base f817b95a50b23c1d9fd4fe4585c59208e58fecbd --head 754961f7b370151d79ba0bc726c88dbbc7045f26 --output /private/tmp/hm2-review-completion-codex-20261015/clean/workspace/scope.json` — 성공.
- 실행: `python3 .eval-plugins/review/skills/review-code/scripts/review_result.py validate --worktree /private/tmp/hm2-review-completion-codex-20261015/clean/source --base f817b95a50b23c1d9fd4fe4585c59208e58fecbd --head 754961f7b370151d79ba0bc726c88dbbc7045f26 --result /private/tmp/hm2-review-completion-codex-20261015/clean/workspace/review-result.json --output /private/tmp/hm2-review-completion-codex-20261015/clean/workspace/assessment.json` — 최종 exit 0, complete, gaps 없음. 최초 검증은 필수 comment 누락으로 partial이었으며 `assessment-attempt-1.json`에 보존했습니다. 로컬 결과 필드만 보완했고 외부 코멘트는 작성하지 않았습니다.
- 미실행: 사용자 요청에 따라 대상 코드, 테스트, 런타임 재현, 타입·린트·빌드는 실행하지 않았습니다. 저장소에도 테스트 및 검증 명령 설정이 없습니다.
- 잔여 위험: 외부 소비자가 없어 서비스별 호출 조건과 실제 영향 빈도는 확인하지 못했습니다. 코드 수정, GitHub 쓰기, 설치, 네트워크 접근은 수행하지 않았습니다.
