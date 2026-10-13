# 읽기의 서가 — B 디자인 참조

Status: reference (선택 보존 완료; 브라우저 검증 미실행)
Date: 2026-10-14
Target: 개인 읽기 노트의 기존 태그 탐색·내용 읽기 화면. 의도한 운영 앱 경로는 제공되지 않았으며 이 참조가 운영 구현은 아니다.
Artifact: [index.html](index.html)
Source: [../explore/index.html?variant=B](../explore/index.html?variant=B)
Selection: 이번 사용자 요청에서 “사용자가 B를 선택한 것으로 명시”하고 이 경로로 보존을 지시했다. 이유는 제공되지 않았다. 기본 화면·침묵·작성자 선호로 추론한 선택이 아니다.
Flow basis: [../flow.md](../flow.md), `flow:personal-tag-lookup` revision 1, `ready_for_review`; PRD `prd:personal-tag-lookup` revision 1; 문제 문서 `problem:personal-tag-lookup` revision 1.
Design authority: 프로젝트 루트와 대상에 기존 디자인 문서·앱 스타일·프로젝트 디자인 규칙이 없어 선택된 B의 인라인 구조와 로컬 토큰을 추출했다. 앱 전체 디자인 시스템의 승인은 아니다. 지정된 design-authority / prototype-verification 참조를 적용했다.
Verification: 소스 및 Node VM 로직 검사. 실제 브라우저·시각 검사 미실행.

## 열기

Opening mode: **direct file**. 이 폴더의 `index.html`을 직접 연다. URL 변형 키나 서버·빌드·설치가 필요 없다. CSS, classic script, 합성 샘플을 한 파일에 포함했다. 외부 의존성 및 상대 자산 로딩이 없다. 다른 폴더의 파일을 복사하지 않아도 이 HTML 하나로 동작하도록 작성했다. 직접 열기의 실제 브라우저 동작은 아직 검증하지 못했다.

## 보존할 디자인

‘읽기의 서가’는 기존 태그에서 저장한 생각을 다시 읽는 조용한 개인 읽기 공간이다. 장식적인 서가 애니메이션은 없다. 상단 제목·샘플 표시, 중앙 최대 760px 단계 화면, 1 태그 선택 / 2 결과 확인 / 3 노트 읽기 표시, 명시적 뒤로 가기, 평가용 접힌 시연 설정을 보존한다. 넓은 화면에서도 읽기 폭을 제한하고 600px 이하에서는 바깥 여백과 패널 여백을 줄인다. 긴 제목은 줄바꿈하고 본문은 원래 줄바꿈을 유지한다. 선택한 태그의 결과와 내용에 집중하는 구조이며 A의 분할 화면을 섞지 않는다.

| 상태 / 행동 | 보이는 결과 | 이동 / 초기화 | 근거와 구현 구분 |
| --- | --- | --- | --- |
| 처음 열기 | 기존 태그 4개, 첫 단계 | 태그 선택 → 결과 | FLOW-001; 합성 데이터 |
| 사유 선택 후 디자인으로 변경 | 사유 n1,n2 → 디자인 n3,n4 | 태그 다시 선택 → U 선택 | FR-001 / AC-001·002, 정확 관계 |
| 결과 노트 N 선택 | N의 샘플 저장 내용 | 결과로 → 이전 N 버튼에 포커스 복원 | FLOW-002, FR-002 / AC-003 |
| 내용 읽기 실패 설정 후 N 선택 | N의 제목과 내용 열기 실패 | 결과로, 다른 노트 선택 | FLOW-002 / AC-004; 다른 본문을 보여주지 않음 |
| 보관 선택, 조회 성공 | 조회 완료 · 0개, 해당 태그 노트 없음 | 태그 다시 선택 | FLOW-003, FR-003 / AC-005 |
| 조회 실패 설정 | 태그 조회 실패, 결과 유무 미확정 | 태그 다시 선택 | FLOW-004 / AC-006; 빈 결과로 단정하지 않음 |
| 시연 초기화 | 선택·본문·실패 설정 해제 | 태그 선택부터 재생 | 평가용 로컬 제어 |

현재 제품 OD는 없다. AS-001 실제 데이터 접근은 미확인이다. EV-001의 합성 입력, EV-002의 보고된 마찰, DEC-001–005의 의미와 제외 범위를 유지한다. 샘플 데이터는 인메모리이며 저장·네트워크 변이는 없다. 실패 설정의 즉시 재렌더링은 시연 방식이지 자동 재시도 또는 실제 동시 변경 정책이 아니다.

## 토큰

반복되는 의미 역할은 아래 CSS custom property를 사용한다. 모두 B에서 추출한 화면 로컬 제안이며 기존 공용 시스템 값으로 위장하지 않는다. 일부 한정된 레이아웃 값(읽기 폭, breakpoint, grid, 0, 100%)과 컴포넌트별 간격·글자 크기는 해당 선택 구조의 리터럴로 남긴다.

| CSS 속성 | 값 | 출처 / 범위 |
| --- | --- | --- |
| `--bg` | `#f3f1ea` | 선택된 B에서 추출한 화면 로컬 값 |
| `--surface` | `#fffef9` | 선택된 B에서 추출한 화면 로컬 값 |
| `--ink` | `#213d35` | 선택된 B에서 추출한 화면 로컬 값 |
| `--muted` | `#52665e` | 선택된 B에서 추출한 화면 로컬 값 |
| `--accent` | `#28634e` | 선택된 B에서 추출한 화면 로컬 값 |
| `--soft` | `#e4eee6` | 선택된 B에서 추출한 화면 로컬 값 |
| `--line` | `#c3cdc3` | 선택된 B에서 추출한 화면 로컬 값 |
| `--danger` | `#9b3027` | 선택된 B에서 추출한 화면 로컬 값 |
| `--danger-bg` | `#fff0eb` | 선택된 B에서 추출한 화면 로컬 값 |
| `--radius` | `18px` | 선택된 B에서 추출한 화면 로컬 값 |
| `--space` | `24px` | 선택된 B에서 추출한 화면 로컬 값 |
| `--font` | `system-ui,-apple-system,"Apple SD Gothic Neo",sans-serif` | 선택된 B에서 추출한 화면 로컬 값 |
| `--small` | `14px` | 선택된 B에서 추출한 화면 로컬 값 |
| `--body` | `16px` | 선택된 B에서 추출한 화면 로컬 값 |
| `--title` | `clamp(28px,4vw,44px)` | 선택된 B에서 추출한 화면 로컬 값 |
| `--focus` | `3px solid #ac4e12` | 선택된 B에서 추출한 화면 로컬 값 |
| `--shadow` | `0 10px 36px #213d350d` | 선택된 B에서 추출한 화면 로컬 값 |

## 의도적인 차이

| 탐색 원본 | 보존본 | 이유 / 권한 |
| --- | --- | --- |
| A와 B 두 구조 | B만 존재 | 사용자 명시적 B 선택 |
| 하단 이전/다음 비교 패널과 예약 여백 | 제거 | 독립 참조에 불필요한 비교 장치 정리 |
| variant 쿼리·history·popstate·전역 방향키 전환 | 제거 | 변형 선택이 끝난 단독 참조 |
| A 전용 split CSS와 layoutA 함수 | 제거 | 제외된 변형 전용 코드 정리 |
| 탐색 산출물 제목/배지 | 선택된 디자인 / 보존된 디자인 B | 산출물 목적 표시 |

B의 콘텐츠·단계 구조·공유 토큰·읽기/실패 상태·뒤로 가기·시연 제어는 동일하다. 디자인 재해석이나 토큰 색상 변경은 하지 않았다. 초기 B 마크업과 전체 공유 상호작용 코드의 일치를 실제 검사했다. 탐색 원본은 그대로 남아 있다.

## 동작과 접근성

전환은 애니메이션 없이 즉시 일어난다. reduced-motion에서도 읽기 내용을 가리지 않으며 별도의 움직임은 없다. 네이티브 버튼·select·details/summary, 최소 44px 제어 높이, focus-visible 윤곽을 사용한다. 화면 전환 후 제목으로 포커스를 옮기고 결과/태그로 돌아갈 때 원래 제어에 포커스를 복원한다. 오류에는 role=alert를 사용한다. B에는 변형 전환용 전역 키 핸들러가 없다. 실제 키보드/스크린리더 검사는 미실행이다.

## 검증 결과와 남은 일

실행한 증거: [../explore/verification.json](../explore/verification.json), 재실행 스크립트 [../explore/verify.cjs](../explore/verify.cjs). `node explore/verify.cjs`로 최종 두 경로의 실제 스크립트를 읽어 **26개 검사 통과**. Node VM과 최소 DOM 대역을 사용했다. AC-001–006에 대응하는 샘플 집합·본문·실패 로직, 초기화, 변형 로직, 외부 자산 로딩 없음, 보존본에서 A·변형 라우팅·전역 단축키 제거 및 선택 B 코드/초기 마크업 일치를 확인했다. 이 결과는 실제 DOM 클릭이나 운영 수용 테스트 통과가 아니다.

색상 선언값의 수학적 대비: 본문/표면 11.66:1, 보조/배경 5.43:1, 버튼 6.97:1, 오류 6.65:1, 포커스/표면 5.40:1. [../explore/contrast.json](../explore/contrast.json) 참조. 모든 조합이나 렌더링 접근성 적합성을 주장하지 않는다.

Chrome headless 실행은 종료 코드 134로 실패했고 로컬 디버깅 포트도 연결되지 않았다. **미실행:** 최종 file:// 직접 열기, 375/768/1440 시각 검사·스크린샷·겹침/overflow, 네이티브 키보드와 포커스, 브라우저 이력/새로고침, console/resource 오류 및 reduced-motion 환경 확인. 알려진 시각 오류를 관찰한 것은 아니며 시각적으로 검증되었다고 부르지 않는다.

수동 점검 순서: 세 너비에서 이 파일을 직접 열기 → 사유/디자인 정확 결과와 긴 제목 확인 → 각 노트 본문 및 결과로 복귀 → 보관 빈 결과 → 조회 실패와 내용 실패 비교 → 초기화 → Tab/Shift+Tab 및 select 방향키, 포커스 위치 확인. 시연 설정을 펼쳐도 콘텐츠가 잘리지 않는지 확인한다. 이 목록은 제안된 미실행 검사다.

실제 데이터와 태그 관계·본문 접근(AS-001), 실제 오류 전달, 실사용 접근성 및 사용성 검증과 운영 구현은 별도 작업이다. 시장 검증·속도 측정·독립 gate·구현 승인·게시를 수행하지 않았다.

## 입력과 전이 의존성 동일성

선택 날짜는 2026-10-14, 근거는 이번 요청이다. 원자료 revision은 알려지지 않았고 아래 내용 해시로 기록한다. PRD와 문제 문서는 revision 1이다. 스킬/참조는 이번 작업에서 읽은 로컬 파일이다. CSS·script·샘플은 탐색 HTML 내부에 있어 HTML 해시가 함께 식별한다. 외부 자산 전이 의존성은 없다. 후속 변경 시 이 해시와 선택·대상을 비교하고 사용자 편집을 보존해야 한다.

| 입력 경로 | SHA-256 |
| --- | --- |
| `chain-notes.md` | `9e447b45b313241b2ef36b025ced1afb8c5283f6aa64b2252117072602f4d952` |
| `problem.md` | `8114c218f484be38a37ecf4de2a25c879553dcd94447d3cc7c936b935fe75aa7` |
| `prd.md` | `d0abcd2f4362980933aaa06f170abe82d30360cd7467b7dc9326b0da18f9a87b` |
| `flow.md` | `c9c176e588964f62834dd8bde7f4b2f22939cb9789453aac1fed284a5d368f5d` |
| `explore/index.html` | `ddbec803c9150e5a79bf1937f515cc84d3a45f21f341e9cd53bbe8a3dc6062d4` |
| `.eval-plugins/product/skills/flow-spec/SKILL.md` | `2f1e69453efa12c89574d92e25d1761e7b5886e8dd99bc522c67ae38c620643c` |
| `.eval-plugins/product/references/artifact-contract.md` | `6e144dc61f8e19b637fbb6d8acd6473b20eced947ab220b921774332cf933669` |
| `.eval-plugins/product/references/flow-template.md` | `84d5375efe7225ab1c455bded69da33d1590ef55208513dd26eaacf38e48901a` |
| `.eval-plugins/design/skills/prototype-explore/SKILL.md` | `0fb098ccf9944954dc3e6e2cb17f794066dd7c80b3579b60b84798bdeaccb71b` |
| `.eval-plugins/design/skills/prototype-promote/SKILL.md` | `811e020ab40b7f4312e8c1fa75df890f4534ad0c0373173b0bb8ab53e55bc459` |
| `.eval-plugins/design/references/design-authority.md` | `222aa1044520b77674f7208e73a5012c29ae56e8a23172fe9ad72e5a7a69eb6f` |
| `.eval-plugins/design/references/prototype-verification.md` | `6dff0d49132fa9285a01b9bab3d21154642855de77d9255829dcc71f37e4e8f8` |
| `.eval-plugins/design/skills/prototype-promote/references/reference-note.md` | `81fbe4c31cde0ba130eabe8b848661a8bf9010e329da156d47feba158ced6e35` |

보존 HTML SHA-256: `1fd9255b8030c24cef373acd3a5827eb5a0855d6b99b82f98ae8debfb91a445c`.
