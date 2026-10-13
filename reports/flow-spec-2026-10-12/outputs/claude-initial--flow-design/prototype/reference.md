# 태그로 노트 찾기 design reference

Status: draft (선택 변형은 캡처됨. 브라우저 검증이 수행되지 않아 `reference` 로 올리지 않음)
Date: 2026-10-12
Target: 개인 태그 조회 화면(구현 대상 앱·경로 미지정). 이 문서는 디자인 참조이며 프로덕션 구현이 아니다.
Artifact: `prototype/index.html` (direct file, 외부 의존성 없음)
Source: `explore/index.html` 변형 B (`?variant=B`, 단일 열 드릴다운). 내용 digest 미계산.
Input revisions: `flow.md` flow:personal-tag-lookup revision 1; `prd.md` prd:personal-tag-lookup revision 1 (sha256 접두 d0abcd2f43629809); `problem.md` revision 1 (8114c218f484be38); `chain-notes.md` revision 미상 (9e447b45b313241b). 디자인 authority 문서(DESIGN.md 등)는 작업 폴더에서 발견되지 않음.
Selection: 사용자가 이번 합성 평가 요청에서 변형 B를 선택한다고 명시함(현재 호출의 요청문). 선택 이유는 제공되지 않음.
Flow basis: `flow.md` FLOW-001–004, FR-001–003, AC-001–006. 미해결 OD 없음. 재시도·권한·정렬은 정책으로 정하지 않음.
Design authority: 없음. 아래 토큰은 선택된 프로토타입에서 추출한 로컬 값이며 앱 전체 디자인 시스템이 아니다.
Verification: 소스 작성 후 브라우저 실행, 뷰포트, 상호작용, 콘솔 검증은 **미실행**. 아래 참조.

## Open the reference

Opening mode: direct file. `prototype/index.html` 을 브라우저로 직접 연다. 클래식 인라인 스크립트만 사용하며 `fetch`/모듈 import/외부 URL이 없도록 작성했다. 실제 `file://` 열기는 이 세션에서 실행하지 못했다. 서버 명령은 필요 없다.

## Design to preserve

목적: 개인이 기존 태그를 선택해 해당 태그의 노트만 보고, 노트를 열어 저장된 내용을 확인한다. 위계는 위에서 아래로 한 열이다: 헤더(제목, 처음으로) → 1. 태그 선택(버튼 그룹) → 2. 결과 또는 노트 리더. 노트를 열면 결과 목록 자리에 리더가 대체해 나타나고 "← 결과로" 로 돌아온다. 태그 영역은 항상 보인다.

| State / action | Visible result | Transition / reset | Implementation note |
| --- | --- | --- | --- |
| 초기 | 안내 문구 (태그 선택 유도) | 태그 선택 | FLOW-001 진입 |
| 태그 선택, 노트 있음 (AC-001/002) | "N개" 결과 목록. 다른 태그 선택 시 목록이 교체되고 열린 노트는 닫힘 | 노트 선택 또는 태그 변경 | 샘플 데이터의 태그 관계로 필터. 실제 데이터 아님(AS-001) |
| 노트 선택, 읽기 성공 (AC-003) | 리더에 선택 노트의 제목, 태그, 내용 | "← 결과로" | 데모 로컬 상태 |
| 노트 선택, 읽기 실패 (AC-004) | 붉은 실선 박스 "⚠ 노트 내용 열기 실패" | "← 결과로" | 시연 노트 「우주의 크기」. 재시도 없음 |
| 태그 선택, 노트 없음 (AC-005) | 회색 점선 박스 "∅ 결과 없음", 조회 성공 명시 | 다른 태그 | 시연 태그 `#보관함` |
| 조회 실패 (AC-006) | 붉은 실선 박스 "⚠ 조회 실패", 노트가 없다는 뜻이 아님 명시 | 다른 태그 | 시연 태그 `#조회오류`. 결과 없음과 모양, 아이콘, 문구가 모두 다름 |
| 처음으로 | 선택 해제, 초기 상태 | — | 리셋 |

## Tokens

CSS custom properties 는 `:root` 에 선언되어 있으며 `--color-bg #f6f4ef`, `--color-surface #fff`, `--color-ink #1f2328`, `--color-muted #5b6470`, `--color-line #d5d0c4`, `--color-accent #1f5f8b`, `--color-selected #e3eef6`, `--color-empty-bg #f1efe8`, `--color-empty-line #8a8577`, `--color-fail-bg #fdecea`, `--color-fail-line #b3261e`, `--color-fail-ink #7a1510`, `--radius 8px`, `--gap 16px`, `--tap-min 44px`, `--measure 720px`, `--font system-ui…`. 권위: 프로토타입 로컬 값(디자인 문서 없음). 명암비는 측정하지 않음.

## Intentional differences

| Source behavior / value | Reference behavior / value | Reason and decision source |
| --- | --- | --- |
| 변형 전환 하단 바, `?variant=` 라우팅, 좌우 화살표 단축키, 탐색용 배너 | 제거 | 승격 규칙. 선택된 변형 B만 보존 |
| 변형 A 전용 스타일/뷰(`.a-*`, `viewA`) | 제거 | 패자 변형 전용 |
| 토큰 이름 `--bg`, `--ink` 등 축약명 | `--color-*` 의미 이름으로 변경, 리터럴 `720px`/`44px`/`16px` 를 토큰화 | 아티팩트 정리. 값은 동일 |
| 하단 스위처를 위한 `padding-bottom:96px` | `--gap` 패딩 | 스위처 제거에 따른 정리 |
| 데모 상호작용 코드(`mount` 등) | 단일 `view`/`draw`/클릭 핸들러로 단순화 | 아티팩트 정리. 동작 동일 |

## Motion and accessibility

애니메이션 없음. `prefers-reduced-motion` 에서 transition/animation 비활성 규칙이 있다. 모든 조작은 `<button>`으로 키보드 접근 가능하며 `:focus-visible` 외곽선, 최소 44px 높이, 태그 `aria-pressed`, 결과 영역 `aria-live`, 빈 상태 `role=status`, 실패 `role=alert` 를 작성했다. 상태 구분은 색 외에 선 모양(점선/실선), 아이콘, 문구로도 한다. 키보드 포커스 이동, 스크린리더 읽기, 명암비는 실제로 확인하지 않았다.

## Assets and dependencies

외부 자산, 폰트, 이미지, 네트워크 의존성 없음. 시스템 폰트 스택만 사용. 샘플 노트/태그는 파일 내 배열이다.

## Verification and remaining work

실제 수행: 작성한 소스의 정적 검토(사용자 요청 흐름, FLOW/AC 대응, 외부 참조 없음 설계). 
**미실행**: 브라우저 열기, 375/768/1440px 레이아웃, 콘솔·리소스 오류, 탐색 파일의 변형 URL/뒤로가기/화살표 전환, 키보드 포커스, 명암비, 소스와 결과의 시각 비교, 스크린샷. 이 세션의 셸 도구 호출이 승인 불가로 거부되어 브라우저를 실행하지 못했고, grep/구문 검사도 수행하지 못했다. 따라서 "동작 확인됨"이 아니다.
수동 확인 목록: ① 파일을 직접 열어 태그 5종과 노트 열기/실패를 눌러 본다. ② 세 폭에서 가로 스크롤과 잘림을 본다. ③ Tab/Enter 로 전 과정을 수행한다. ④ 탐색 파일에서 `?variant=A`, `?variant=B` 와 이전/다음, 뒤로가기를 확인한다.
남은 구현 작업: 실제 데이터 읽기(AS-001 미검증), 대상 앱 디자인 시스템 정렬, 문구 확정, 재시도·정렬 등 PRD 미정 사항(제품 결정 없이 추가 금지).
