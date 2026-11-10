# 프로젝트 목록 구현 검증·재개 하네스 설계

이 문서는 설계 산출물이다. 기능 구현, 테스트 실행, 서버·브라우저 실행, helper의 `capture`·`assess`는 수행하지 않았다. 아래 작업과 시나리오는 향후 별도로 승인된 구현 실행을 위한 계획이며 성공 기록이 아니다. 현재 실행의 허용된 쓰기는 이 `design.md`뿐이다.

`implement`의 입력·증거·재개 계약을 설계 근거로 읽었다. 해당 스킬 자체도 “requirements or harness design alone”을 구현 실행 대상에서 제외한다. 따라서 현재 요청을 기능 구현 권한으로 해석하지 않는다. 소스 파일, 기존 문서, 서버, 사용자 초안, Git 상태를 변경하지 않는다.

## 1. 원본과 권한

읽은 애플리케이션 루트는 `/private/tmp/skill-quality-20261110/implement/runs/I5-design/source`다. 아래 상대 경로는 모두 이 루트 기준이다.

| 근거 | 역할 및 적용 |
| --- | --- |
| 현재 `prompt.txt` | 이번 작업은 하네스 설계만 허용. 읽기·쓰기 제한, 실행·설치·Git 변경·외부 게시·위임 금지가 최우선이다. |
| `spec.md` | 제품 요구 AC-1~3. ID와 전체 조건·행동·결과를 보존한다. |
| `AGENTS.md` | 향후 구현 허용 경로는 `src/`, `tests/`. `src/ui.js`·토큰·API 소유자 재사용, 나머지 원문·서버·사용자 초안 보존. 이번에는 해당 경로도 수정하지 않는다. |
| `prototype.html:11–14` | 선택된 참조의 구조: 목록 위 필터와 개수, 목록·선택 패널. 정적 데모의 데이터·초기 선택은 별도 제품 정책을 만들지 않는다. |
| `DESIGN.md` | 앱의 파란색 토큰, 넓은 화면 좌우 배치·좁은 화면 아래 배치, 레이블·키보드 포커스. 참조의 주황색은 토큰 변경 권한이 아니다. |
| `ux.md` | 기존 helper, 목록과 독립된 선택, 로딩/빈 결과/오류 구분, 최신 요청만 렌더, 요청·오류 중 선택 패널 유지. |
| `src/api.js`, `server.mjs` | 실제 GET 계약과 fixture 동작. 데모에서 API를 추정하지 않는다. |

원본 요구의 기준 텍스트는 아래와 같다. 발췌된 짧은 작업명으로 원본을 대체하지 않는다.

> - AC-1: Add a labelled status selector above the list: All, Active, Archived, Paused.
>   Changing it fetches that status through the existing API client and shows matching
>   projects and their result count. Use the selected reference's structure.
> - AC-2: A project can be selected and its name appears in the selected-project panel.
>   Keep the selection when filtering hides that project. Filtering back restores the
>   selected appearance. A successful empty result has its own visible empty state.
> - AC-3: A failed request has the existing error treatment and Retry action, distinct
>   from an empty success. Retry uses the current filter and preserves the selection.
>   The current implementation must not be reported browser-verified without opening it.

향후 실행은 원본 파일 전체 바이트와 현재 요청, 적용된 디자인·UX·참조의 해시 및 경로를 입력 manifest에 고정한다. 요약이나 AC 일부만 복사한 파일을 정본으로 쓰지 않는다. 변경할 구현 코드는 frozen input 대신 baseline·verification snapshot의 대상으로 둔다.

이 `spec.md`는 frontmatter·정형 AC 표·QUESTIONS 연결이 없는 직접 요구 문서다. 파일명만 보고 구조화 SPEC gate를 통과했다고 표시하지 않는다. AC-1~3은 명시적으로 전부 매핑하고 조건·행동·결과를 원문과 대조하되, 임의 산문의 자동 의미 완전성 판정을 주장하지 않는다. 향후 입력이 지원되는 구조화 SPEC로 바뀌면 새 실행에서 원본 AC 및 연결 QUESTIONS의 직접 추출·비교 gate를 적용한다.

## 2. 현재 코드에서 읽은 사실과 한계

아래는 파일 읽기로 얻은 정적 관찰이다. 실제 앱 동작이나 테스트 통과 증거는 아니다.

| 위치 | 실제 읽은 내용 | 이 관찰로 알 수 없는 것 |
| --- | --- | --- |
| `src/app.js:6–12` | `let selected = null;`, `let visible = await projects();`, 선택 콜백에서 `selection.textContent = project.name;` 후 재렌더 | 필터가 아직 없으므로 필터 전환·오류·경합에서 선택 유지가 되는지는 입증하지 못한다. |
| `src/api.js:1–4` | 기본값 `all`, status를 query로 전달, 실패 응답에서 예외 발생 | UI가 해당 client를 올바른 상태로 호출하는지는 별도 확인이 필요하다. |
| `src/ui.js:1–9,12–29` | `selectField`, `renderRows`의 `aria-pressed`, `showProblem`의 alert·Retry 제공 | 존재하는 helper가 현재 앱의 필터·오류 흐름에 연결되었다는 뜻은 아니다. |
| `index.html:5–6` | `#toolbar`, `#rows`, `#selection`과 두 패널이 이미 있다. | 화면의 실제 배치·레이블·반응형 동작은 미확인이다. |
| `src/theme.css:1,5–7` | 파란 `--accent`, 선택 스타일, focus-visible, 700px 이하 단일 열 규칙 | 실제 화면에서의 시각 정합·키보드 경험은 미확인이다. |
| `server.mjs:8,18–24` | All 3건, Active 2건, Archived 1건, Paused 0건. Active 응답은 150ms, 나머지는 20ms 지연. | 현재 서버를 실행하거나 HTTP 응답을 확인하지 않았다. |
| `tests/api.test.mjs:5–12` | mock fetch로 archived 전달과 실패 예외를 검증하는 기존 테스트 | UI, 선택 유지, 최신 응답, 실제 API 연동을 검증하지 않는다. 테스트 자체도 이번에는 실행하지 않았다. |

현재 구현에는 필터·개수·로딩·빈 결과·오류/Retry 연결이 보이지 않는다. 일부 선택 코드가 있다는 이유로 AC-2 전체를 구현 또는 검증 완료로 올리지 않는다. 보존 대상인 “사용자 초안”의 구체 파일·내용은 현재 읽은 자료만으로 특정하지 못했으므로 추정하지 않는다. 향후 baseline에서 기존 변경 전체를 보호하고, 해당 파일이 확인되면 그 상태도 보존 목록에 포함한다.

## 3. 원본 → 작업 → 코드 및 행동 증거

아래 T 항목은 계획된 작업이다. 기존 코드를 충족 여부에 따라 재사용하고 불필요하게 다시 쓰지 않는다. `src/app.js`가 상태·요청·화면 연결을, `src/api.js`가 API 접근을, `src/ui.js`가 UI helper를 소유한다. 입력 문서·`index.html`·서버 변경은 계획하지 않는다.

| 원본 요구/규칙 | 향후 작업 | 향후 코드 증거 | 요구 결과를 구별하는 확인 |
| --- | --- | --- | --- |
| AC-1 전체 | T1: `#toolbar`에 `selectField`로 Status와 네 옵션·개수를 연결. 상태 변경 → `projects(status)` → 표시 목록·개수 갱신. 참조의 필터/개수 구조 적용. | 실제 수정본의 옵션·이벤트 → API client 호출 → 결과/개수 렌더 경로를 파일·행·정확한 전체 행 인용으로 연결 | C1 기존 API 계약 + B1 실제 앱에서 네 status의 요청과 표시 데이터·개수 확인 + S1 참조 구조·토큰 추적 |
| AC-2 전체 | T2: 선택 프로젝트 상태를 visible 결과와 독립 유지. 성공 0건 화면 마련. 필터 복귀 시 동일 ID의 선택 표시 복원. | 선택 상태 소유자와 패널 갱신, `renderRows` selectedId 전달, 빈 성공 분기 인용 | B2 Tide 선택 → Archived → All; 패널 Tide 유지·복귀 시 눌림 상태. B3 Paused 성공 0건의 빈 화면과 선택 유지 |
| AC-3 전체 | T3: 요청 실패를 `showProblem`으로 연결하고 Retry가 현재 status를 재요청하도록 구성. 요청·오류 중 선택 유지. | 실패 분기·Retry 콜백·현재 필터 참조와 선택을 지우지 않는 경로 인용 | B4 실제 API 실패 → 오류/Retry → 복구. 요청 status·패널 유지·빈 성공과의 차이 확인 |
| `ux.md` 로딩·최신 응답 규칙; AC-1~3에 영향 | T4: 로딩을 별도 상태로 표시. 요청 순서/취소 등의 기존 구조에 맞는 방식으로 오래된 성공·실패가 최신 상태를 덮지 않게 구성 | 상태 전이와 stale 응답 방어의 실제 경로 인용. 구현 방식을 선결정된 요구로 취급하지 않음 | B5 Active 다음 Archived를 빠르게 선택. 늦은 Active 응답 후에도 Archived 1건 유지. 제어 가능한 경합 테스트로 오래된 실패도 최신 성공을 덮지 않음 확인 |
| `DESIGN.md`, `ux.md` 및 참조 구조 | T5: 기존 UI helper와 토큰을 유지하고 필요한 스타일만 `src/`에서 조정 | helper 재사용, `--accent/--surface/--line/--space`, 반응형·focus 규칙 추적 | S1 + B6 넓은/좁은 화면 배치, 선택 파란색, 레이블·키보드 포커스 확인 |
| 입력·기존 사용자 작업 보존 | T0/T6: 실행 전 baseline과 실행 후 diff·증거 연결, 원문 AC별 리뷰·평가·재개 기록 | 모든 변경 경로·초기 dirty 내용·입력 바이트 비교 | S2 허용 범위·원문/서버/초안 보존 검사. 자동 검사만으로 editable dirty 파일 내부의 사용자 의도 보존까지 증명했다고 하지 않음 |

T0 → T1~T5 → verification target 캡처 → C/S/B 확인 → T6 평가 순서로 설계한다. 수정이 발생하면 새 verification target을 만들고 영향받는 확인을 다시 수행한다. 초기 dirty 파일과 작업이 겹치는 경우 향후 요청이 그 겹침까지 허용하는지 확인한 뒤 `editable_dirty`에 명시하고 실제 diff를 읽는다. 깨끗한 상태를 만들려고 reset/stash하거나 사용자 변경을 제거하지 않는다.

## 4. 향후 검증 절차와 증거 계약

각 check에는 required 여부와 관찰 결과를 사전에 선언한다. UI 작업이므로 실제 앱 브라우저 확인은 필수다. 테스트 통과나 정적 참조 화면만으로 이를 대체하지 않는다.

- **C1**: 소스 루트에서 기존 `npm test`. 실제 argv, cwd, 종료 코드, stdout/stderr를 보관한다. 이 테스트의 입증 범위는 API client 계약이다. T4의 경합 등을 자동화할 경우 실제 상태·렌더 결과를 구별하는 최소 테스트만 `tests/`에 추가하는 계획이며, 구현을 그대로 복제한 테스트로 대체하지 않는다.
- **S1**: 요구 원문과 현재 코드의 조건·행동·결과·UI/API 경로·검증 목적을 대조한다. `prototype.html`의 주황색은 의도된 차이로 기록하고 앱 파란 토큰을 사용한다. helper·코드 인용의 존재만으로 의미가 맞다고 판정하지 않는다.
- **S2**: 입력 바이트·실제 변경 목록·허용 경로·보존 파일·초기 사용자 변경을 비교한다. 적용 범위 위반은 별도 기록하고 사용자 작업을 버려서 해결하지 않는다.
- **B1~B6**: 향후 실행이 허용된 경우 `PORT=0 npm start`가 출력하는 실제 loopback URL의 `/`를 연다. 고정 포트나 프로토타입 URL을 결과로 꾸며 넣지 않는다. 도구 이름, 실제 URL, viewport, 데이터·상태·행동 순서와 관찰, 브라우저/네트워크 trace 및 필요한 캡처를 기록한다. 예시 viewport는 넓은 화면 1280×900, 좁은 화면 390×844다. 실행 시 실제 값을 기록한다.

브라우저 시나리오의 구체 조건:

1. **B1** All: Tide/Forest/North 3건, Active: Tide/North 2건, Archived: Forest 1건, Paused: 0건. 레이블·옵션·목록 위 위치·개수·`status` query를 확인한다. 단순히 텍스트가 바뀌는 것뿐 아니라 기존 client를 통한 실제 요청과 응답 렌더를 연결한다.
2. **B2/B3** All에서 Tide를 클릭해 패널과 `aria-pressed`를 확인한다. Archived로 숨겨도 패널 Tide 유지, All 복귀 시 Tide 선택 표시 복원. Paused의 성공 응답에서는 0건·명시적인 빈 결과를 표시하고 오류/Retry와 구별한다.
3. **B4** 선택을 둔 채 fixture 전용 `PUT /__fixture__/mode`의 `{"fail":true}`로 오류를 유도한다. 현재 필터의 GET 실패와 기존 alert·Retry를 확인한다. 오류 상태에서도 필터를 변경한 뒤 `{"fail":false}`로 복구하고 Retry하여 **현재** status query·결과와 기존 선택 유지를 확인한다. fixture 설정은 UI나 제품 기능에 추가하지 않고, 실행 후 원래 정상 상태로 복구한다. 이번에는 이 요청을 보내지 않았다.
4. **B5** Active 요청 직후 Archived를 선택하여 150ms/20ms 순서를 이용한다. 최종 Archived 목록·개수가 유지되는지 관찰한다. 로딩 중 패널과 필터 사용성을 확인하고 로딩을 빈 결과로 오인하지 않게 한다. 오래된 실패/반복 Retry 경합은 명시적인 응답 순서 제어가 가능한 확인 환경에서 보완한다. 환경이 없으면 해당 경로를 미검증으로 남긴다.
5. **B6** 각 viewport에서 넓은 화면의 좌우 두 패널·좁은 화면의 목록 아래 선택 패널, Status의 접근 가능한 레이블, Tab 이동·select 조작·행/Retry 키보드 조작·보이는 focus와 파란 선택 표시를 확인한다.

행동 증거는 각 시나리오의 실제 결과를 담아야 한다. 화면 한 장은 요청 query, 선택 지속, 응답 경합을 단독 입증하지 못한다. 시나리오마다 같은 전역 상태를 암묵적으로 물려받지 않도록 시작 filter·selected ID·fixture fail 상태를 기록한다.

향후 기록 구조는 다음과 같다. 현재 이 파일들을 생성하거나 경로가 존재한다고 주장하지 않는다.

- `inputs.json`: 원본 sources·해시, AC-1~3의 안정 ID, 직접 UX/디자인 근거 anchor, 요구별 checks, `surface: ui`, `scope: [src, tests]`, preserve 및 승인된 dirty 겹침.
- `baseline.json`: 편집 전 입력·HEAD·index·실제 작업 파일 바이트·초기 사용자 변경. 실행 가능한 환경과 권한이 있을 때 신뢰된 candidate helper로 새 파일에 캡처한다.
- `verification-target-N.json`: 편집 후, 확인 실행 전에 동일 입력으로 캡처한 정확한 대상 digest.
- `evidence/attempt-N/`: 실제 명령 출력·브라우저 trace·관찰·정적 대조 기록. 비어 있지 않은 파일의 실제 SHA-256을 기록하고 대상 digest에 연결한다.
- `result-N.json`: baseline 대비 모든 실제 변경 경로, 각 요구의 disposition·이유·현재 코드 정확 인용, 각 check의 status·세부사항·실제 증거. passed는 target digest와 증거 경로·해시를 필수로 갖는다. top-level 완료 값을 사람이 써 넣지 않는다.
- `assessment-N.json`: 신뢰된 helper `assess`의 실제 산출물과 종료 코드. 실행하지 못하면 “평가 미수행/이용 불가”로 남기고 가상의 digest·통과 결과를 만들지 않는다.

상태·기록은 향후에도 앱 checkout 밖의 승인된 경로에 저장한다. helper는 Git checkout 등의 전제조건이 있으며 현재는 실행·Git 작업을 하지 않았다. 비-Git/미지원 환경이면 기계 평가 불가 사실을 남긴다. 검증을 통과시키려고 Git을 초기화하거나 설치·서비스·리뷰 하네스를 시작하지 않는다. 리뷰 알림은 기존 설정과 별도 권한이 있는 경우에만 다루며 이번 설계에서는 발송하지 않는다.

## 5. 미결·미수행·입력 변경의 구분

요구 구현 상태, check 실행 상태, 입력/대상 유효성은 서로 다른 축으로 기록한다.

| 상황 | 기록과 처리 | 완료에 미치는 영향 |
| --- | --- | --- |
| 제품 정책·선택 근거가 미결 | 해당 AC를 `needs_decision`, 질문·출처·영향 AC·필요 답변으로 기록. 독립 작업은 진행 가능. | 요구가 실제로 해결되기 전 해당 AC 완료 불가 |
| 코드 경로 자체가 없음 | `unimplemented`와 빠진 행동·남은 T 항목 기록 | 미구현이며 검증 도구 부재와 혼동하지 않음 |
| 코드 증거는 있지만 브라우저 없음/실행 금지 | 구현 주장은 확인한 코드 범위로 한정, B checks `not_run`과 정확한 이유 기록 | 향후 구현 평가에서는 필수 UI 확인 누락으로 partial. 현재는 설계만 했으므로 평가 status 자체를 산출하지 않음 |
| 실행한 확인이 실패 | check `failed`, 실제 출력·재현 상태·원인 후보 보존. 수정 후 새 target·새 attempt | 기존 실패를 지우거나 required를 약화하지 않음 |
| 명시적 제외 | 원래 AC ID를 남기고 사전에 승인된 source·정확한 인용으로만 `excluded` | 실패 후 임의 제외는 허용하지 않음. 이번 설계 요청은 AC를 삭제한 것이 아니라 구현 실행을 요청하지 않은 것 |
| 입력 문서/참조/요청 또는 HEAD 변경 | 기존 실행의 완료 근거가 최신이 아님을 기록. 원본 변경분과 AC 영향 대조 후 새 run baseline | 기존 증거를 새 입력의 통과로 전용하지 않음; 불일치는 invalid 대상 |
| 입력은 같고 코드 변경 | 새 verification target, 영향 확인 재실행. 정확한 전체 digest가 달라졌다면 기존 passed를 새 digest로 수동 이식하지 않음 | 변경된 대상에 대한 현재 증거가 있어야 함 |
| 새 사용자 작업 또는 보존 위반 | diff·현재 바이트 보존, 권한·변경 범위 재조정. 되돌리기로 사용자 작업 제거 금지 | 범위/보존 위반은 별도 invalid 사유로 드러냄 |

원문은 네 옵션, 토큰 권한, 선택 유지, 오류/빈 결과 구분, 최신 응답 정책을 이미 정하고 있다. 이를 다시 미결로 만들지 않는다. 초기 선택을 데모처럼 Tide로 강제하는 정책은 명시되지 않았으므로 데모에 맞추려 기능을 추가하지 않는다. 경합 확인 도구 부재는 제품 의사결정이 아닌 검증 환경의 미확인으로 기록한다.

## 6. 재개와 평가 경계

재개 시 이전 manifest·snapshots·결과·실제 traces를 먼저 읽고 현재 요청 권한, 입력 원본·참조, HEAD·index·작업 파일과 비교한다. 이번 요청이 유지되면 구현·테스트·브라우저를 시작하지 않는다. 향후 구현이 승인되면 위 T0부터 실제 baseline을 새로 수립한다. 이 설계 파일이 기존 실행의 baseline을 대신하지 않는다.

입력/HEAD가 달라지면 별도 run을 열고 AC-1~3의 ID와 이전 미결·실패·증거를 유지하며 변경 이유를 기록한다. 입력이 같아도 코드가 달라졌으면 새 target을 캡처한다. 이전 실패를 없애거나 과거 실행을 덮어쓰지 않는다. 요구 원문 → T 항목 → 현재 코드 인용 → 해당 target의 실제 check 증거가 끝까지 이어지는지 다시 확인한다.

향후 helper가 산출하는 `complete`는 입력·범위·요구 연결·선언된 확인이 충족된 구현 평가다. `partial`은 미구현·필수 미수행/실패·결정 대기를 드러내며, 모든 요구가 결정에 막혔고 산출 변경도 없는 경우의 `blocked`와 구분한다. `invalid`는 입력/대상/증거 불일치·기록 모순·범위/보존 위반이다. 이번 작업에서는 이 중 어느 기계 판정도 실행하거나 부여하지 않았다.

helper는 해시·경로·정확 인용·기록 정합성을 검사할 수 있으나 실제 도구가 실행되었는지, 의미가 맞는지, UI가 참조에 적절한지는 인증하지 못한다. 원문 대조와 실제 행동 traces가 필요하다. 별도 코드 리뷰·Visual QA·배포 승인·외부 게시를 수행했다는 뜻도 아니다.

현재 제공한 것은 이 하네스 설계와 소스에 대한 정적 관찰뿐이다. 다음 실제 구현 실행에 필요한 것은 변경된 요청 권한에 맞는 baseline, 코드 변경, 실제 명령·앱 브라우저 증거, 그리고 그 동일 대상을 평가한 결과다.
