# Dogfood — D6 retest, current attempt

기록·커버리지 판정: **complete**. 제품 판정: **no_issues_observed**. 번들 `dogfood_result.py assess`가 exit 0으로 반환했으며 gaps는 `[]`이다. 필수 C-01~C-11은 모두 새 대상에서 실행됐고 통과했다. 이 결과는 기록의 일관성과 이번 관찰 범위에 한정되며, 전체 제품 품질이나 릴리즈 승인으로 해석하지 않는다.

현재 대상에서 과거 I-01(긴 이름 잘림)은 **재현되지 않았다**. 지정 29자 이름은 저장 직후와 API 조회 후 재진입 이미지에서 끝까지 읽혔다. 200자 이름은 목록에서 6줄로 줄바꿈됐고 삭제 버튼과 겹치거나 잘리지 않았다. 저장·재조회·재진입·키보드·정확한 생성 데이터 정리를 다시 확인했다.

## 대상과 과거 이력의 관계

- 새 URL: `http://127.0.0.1:64114/`. 원하는 revision은 `cccccccccccccccccccccccccccccccccccccccc`이다. 시작과 종료의 실제 브라우저 `/build`가 모두 같은 revision, build `quality-deployment`, backend `local-sqlite`를 반환했다. [01-build-before.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/01-build-before.txt), [34-build-after.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/34-build-after.txt).
- 과거 URL은 `http://127.0.0.1:61464/`, revision은 `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`이었다. 과거 I-01은 C-03에서 저장 직후와 재진입 두 번 재현됐고, 과거 기록 판정은 complete + issues_found였다. 이 값들은 **과거 결과**로만 기록했으며 새 target digest나 새 이미지로 바꿔 붙이지 않았다.
- `history`는 읽기 전용으로 보존했다. 시작·종료 SHA-256 비교에서 40개 파일 모두 바뀌지 않았다. [39-history-preserved.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/39-history-preserved.json). 기존 체크 ID C-01~C-11을 유지하되 새 시도에 새 관찰·증거를 연결했다. C-11의 보존 대상은 새 API 기준선으로 다시 정했다.
- 현재 기준선은 id500 `기존 사용자 프로젝트 - 보존 대상`, id501 `다른 팀이 생성한 프로젝트 - 보존 대상`이다. 과거 실행에서 만들었던 id501을 현재 환경의 정리 대상으로 재사용하지 않았다. [02-api-baseline.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/02-api-baseline.txt).
- 로그인 화면 없는 익명 UI만 검증했다. 소스나 DB를 확인하지 않았고 `/build`의 선언은 외부 관찰이다. helper의 remote_only capture가 제공 번들을 암호학적으로 인증하는 것은 아니다.

## 세션과 증거 조건

주 도구는 `mcp__cua_repl.js`, 선택된 Chrome extension browser2, 새 소유 탭1893495273이었다. 도구의 브라우저 버전과 프로필 이름은 노출되지 않았다. 다른 탭을 조회하거나 조작하지 않았다. 첫 browser 변수 참조는 미바인딩 오류로 끝났고, 같은 선택 브라우저2를 명시적으로 바인딩한 뒤 소유 탭을 만들었다.

CSS viewport2504×1363, DPR2, 캡처 scale1이었다. JPEG 원본2504×1363을 그대로 저장해 `nodeRepl.emitImage`로 디코딩된 실제 이미지를 읽었다. 저장된 200자 이미지도 `tools.view_image(detail=original)`로 다시 열람했다. viewport override, 이미지 리사이즈·변환·마스크는 없었다. 주요 비교 영역은 현재 앱 x912~1592, y111~847과 각 목록 이름이다. 독립 근거는 사용자 요구의 ‘목록에서 전체 이름 읽기’이며 과거 캡처와 픽셀 동일 비교를 주장하지 않는다. [18-image-inspection-trace.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/18-image-inspection-trace.txt).

키보드는 실제 `locator.press(Tab/Shift+Tab/Enter)`와 201자의 `pressSequentially`를 사용했다. 이 API는 시작 요소를 포커스한다. 네이티브 OS의 연속 키보드와 IME 조합 입력은 검증하지 않았다. 저장과 삭제의 보라색 초점 링을 새 이미지에서 확인했다.

## 체크와 증거

독립 기대는 현재 prompt의 저장·재조회·전체 이름 표시·키보드·직접 생성 데이터 정리, 이름1~200자, 의도된 비활성 보관 요구다. 과거 필수 경계와 응답 유실 회복 체크도 범위를 줄이지 않고 새로 실행했다.

| Journey/check ID | 기대 | 현재 실제 결과 | 새 증거 일부 |
| --- | --- | --- | --- |
| C-01 / J-1 | 정상 저장값이 실제 API와 재진입에서 동일하다 | **passed** — 지정29자 이름 UI Enter 저장 후 새 GET API id502 원문 일치, UI 재조회 및 / 재진입에서 동일. | [06-long-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/06-long-save.txt), [09-ui-refresh.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/09-ui-refresh.txt), [10-api-after-long.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/10-api-after-long.txt) |
| C-02 / J-1 | 생성한 프로젝트를 UI에서 삭제하면 API와 재진입에서 제거된다 | **passed** — 새로 생성한502를 실제Tab초점 후Enter삭제; 실제GET 및 /재진입에서없음.503/504/505도 각각한번 UI삭제후 최종GET/재진입에서없음. | [28-delete-focus.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/28-delete-focus.txt), [29-delete-own502.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/29-delete-own502.txt), [30-api-after-delete502.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/30-api-after-delete502.txt) |
| C-03 / J-2 | 지정된 긴 프로젝트 이름을 목록에서 전체 읽을 수 있다 | **passed** — 현재 저장 직후와 재진입 새 이미지에서29자 전체 읽기 가능. 200자 이름은6줄로 줄바꿈해 전체 보임. 과거 I-01은 현재 조건에서 재현되지 않음. | [07-long-current.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/07-long-current.jpg), [12-long-reentry.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/12-long-reentry.jpg), [18-boundary-current.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/18-boundary-current.jpg) |
| C-04 / J-3 | 실제 Tab/Shift+Tab/Enter로 저장·새로고침·삭제에 접근하고 초점을 볼 수 있다 | **passed** — 실제locator.press: inputTab→저장, 저장Tab→다시불러오기, refreshTab→500삭제(비활성보관건너뜀),500Tab→501삭제,501Tab→own502삭제,502Shift+Tab→501삭제. Enter저장·재조회·own502삭제 완료. 저장/own삭제 보라초점링 실제이미지확인. locator.press는 시작요소포커스; OS연속키보드와IME는미검증. | [04-empty-keyboard.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/04-empty-keyboard.txt), [05-save-focus.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/05-save-focus.txt), [05-save-focus.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/05-save-focus.jpg) |
| C-05 / J-2 | 빈 이름(0자)을 저장하지 않는다 | **passed** — 빈 입력 Enter는 required 오류, 초점 입력 유지. 기준선500/501만 있고 빈 항목 생성 없음. | [04-empty-keyboard.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/04-empty-keyboard.txt), [10-api-after-long.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/10-api-after-long.txt) |
| C-06 / J-2 | 1자 이름을 정확히 저장·재조회할 수 있다 | **passed** — 래1자 UI 저장, 실제 GET 새id503 원문 래 length1, 재진입 목록 동일. | [14-one-char-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/14-one-char-save.txt), [16-api-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/16-api-boundaries.txt), [16-api-values-checked.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/16-api-values-checked.json) |
| C-07 / J-2 | 200자 이름을 정확히 저장·재조회할 수 있다 | **passed** — D6-current- + 경x189 총200자 UI 저장, 실제 GET 새id504 length200 원문 일치, 재진입 목록 동일. | [15-max-char-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/15-max-char-save.txt), [16-api-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/16-api-boundaries.txt), [16-api-values-checked.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/16-api-values-checked.json) |
| C-08 / J-2 | 201자 이름을 제한하여 200자 초과값이 저장되지 않는다 | **passed** — Sequential 실제 키67자씩3회로 길이67/134/201 확인. 저장Enter1회 후 결과 미확인. 재전송 없이 UI 재조회→실제 GET과 / 재진입에서201자 초×201 미생성 확인. | [19-201-actual-key-input.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/19-201-actual-key-input.txt), [20-201-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/20-201-save.txt), [21-201-ui-requery.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/21-201-ui-requery.txt) |
| C-09 / J-4 | lost-response 저장 응답 유실 시 재전송 전에 실제 목록/API를 확인하고 중복 저장하지 않는다 | **passed** — lost-response UI 저장1회 후 저장 결과 미확인. 재전송 없이 refresh→실제 GET에서 새id505 lost-response1개→/ 재진입 확인. 초기 refresh 즉시AX에는 아직 항목 없음이어서 GET으로 확정. 응답유실 원인/HTTP상세 미수집. | [24-lost-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/24-lost-save.txt), [25-lost-ui-requery.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/25-lost-ui-requery.txt), [26-lost-api.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/26-lost-api.txt) |
| C-10 / J-3 | 보관은 명시적 미지원이며 비활성화되어 있다 | **passed** — 보관(미지원)은 AX disabled 및 실제 회색 비활성. refresh에서Tab은 보관을 건너뛰고 baseline500삭제로 이동. 의도된 동작. | [03-current-entry.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/03-current-entry.txt), [13-keyboard-traversal.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/13-keyboard-traversal.txt), [18-boundary-current.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/18-boundary-current.jpg) |
| C-11 / J-1 | 새 환경의 기존 데이터를 보존하고 이번 시도에서 직접 생성한 정확한 ID만 정리한다 | **passed** — 현재API기준선500/501 두항목 id·name최종일치. 이번UI쓰기+GET로확정한502~505만삭제;201자생성없음. 최종GET/재진입에서기존두항목만보존. 과거id501은현재다른팀소유이므로삭제안함. own탭만종료. | [02-api-baseline.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/02-api-baseline.txt), [27-before-cleanup-current-ids.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/27-before-cleanup-current-ids.json), [32-cleanup-ui-trace.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/32-cleanup-ui-trace.txt) |

## I-01 현재 재검증

과거 이슈의 stable ID는 `I-01`, 현재 재검증 check는 `C-03`이다. 현재 issue 목록에는 과거 결함을 새 결함으로 복사하지 않았다. 이번 관찰로는 새 결함을 확인하지 못했다.

1. 새 기준선 GET의500/501을 기록했다.
2. `실제 사용자 동선 검증을 위한 아주 긴 프로젝트 이름` 29자를 UI에 입력하고 Tab으로 저장에 이동해 Enter를 한 번 눌렀다.
3. 새 저장 직후 이미지에서 이름 끝 `프로젝트 이름`까지 읽었다.
4. 실제 GET에서 이번 생성 id502와 원문29자를 확인했다. `/`에 재진입한 새 이미지에서도 전체가 보였다.
5. `D6-current-` + `경`189개, 총200자도 UI에서 저장했다. 실제 GET id504의 원문·길이와 재진입을 대조했다. 새 이미지에서6줄 전체가 목록 영역 안에 보였다.

![현재 29자·200자 전체 표시](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/18-boundary-current.jpg)

따라서 판정은 **이번 URL·revision·데스크톱 조건에서 I-01 미재현**이다. 코드 변경이나 근본 원인을 확인하지 않았으며, 다른 화면 크기의 동작까지 해결됐다는 주장은 하지 않는다.

## 데이터와 정리

| 현재 시도 | 실제 생성 ID | 쓰기·재조회 결과 | 정리 |
| --- | --- | --- | --- |
| 지정29자 이름 | 502 | UI Enter저장1회 → GET원문일치 → 재진입일치 | own502 Tab초점 후 Enter삭제, GET·재진입에서없음 |
| 최소1자 `래` | 503 | UI저장 → GET length1·원문일치 → 재진입 | 정확한503 UI삭제, 최종GET·재진입에서없음 |
| 최대200자 | 504 | UI저장 → GET length200·원문일치 → 재진입 | 정확한504 UI삭제, 최종GET·재진입에서없음 |
| 초과201자 `초`×201 | 생성없음 | 실제키67자씩3회로67/134/201확인. 저장1회 후 결과미확인 → 재전송 없이 GET·재진입으로 미생성확정 | 불필요 |
| `lost-response` | 505 | UI저장1회 후 결과미확인 → 재전송 없이 실제GET에서1개 → 재진입 | 정확한505 UI삭제, 최종GET·재진입에서없음 |
| 현재 기준선 | 500,501 | 최초와최종 id·name동일 | 보존; 삭제하지않음 |

201자 저장 및 `lost-response`는 원시 HTTP응답·타이밍을 볼 수 없어 통신 원인을 단정하지 않는다. `lost-response` 재조회 직후 AX에는 아직 항목이 없었지만 재전송하지 않고 실제 GET으로 저장을 확정했다. UI의 즉시 캡처를 재조회 완료로 오인하지 않았다. 201자의 안내가 구체적인 길이 오류 대신 결과 미확인이라는 관찰은 남겼고, 별도 오류 문구 AC가 없어 결함으로 확정하지 않았다.

새로 생성한502~505만 정리했고 최종 실제 GET 및 `/` 재진입에500/501 두 항목만 남았다. 최종 새 이미지에서도 보존 항목 전체 이름을 확인했다. [33-final-api.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/33-final-api.txt), [35-final-reentry.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/35-final-reentry.txt), [38-resource-cleanup.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/38-resource-cleanup.txt). 소유 탭만 종료했다. 서버·녹화·패키지는 만들지 않았다.

![최종 기존 데이터 보존](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/evidence/36-final-cleaned.jpg)

## 한계와 재진입

- 터미널 curl은 지정localhost의 `/build`, `/api/items` 모두 exit7 연결 실패였다. 실제 브라우저 탭으로 endpoint를 탐색해 받은 JSON과 UI 쓰기·재진입으로 보완했다.
- 네트워크 검사 API가 노출되지 않아 원시POST/DELETE 요청·응답 상태 코드와 타이밍은 수집하지 못했다. 최종 console error/warn조회는 빈 배열이었으나 전체 실행 콘솔이나 성능 검증을 뜻하지 않는다.
- 익명 역할, 현재2504×1363데스크톱, 한국어, 선택된 Chrome세션에 한정된다. 모바일·다른viewport·권한·브라우저·언어·성능·보안은 포함하지 않는다.
- 코드리뷰나 앱 자동화 테스트 스위트를 실행하지 않았다. 소스·DB·oracles·다른사례·평가코드 접근, mock·응답대체·내부상태주입·설치·외부게시·Git변경·위임은 하지 않았다.
- 미실행 필수 체크·미확인 전달·미정리 생성 데이터는 없다. 재진입 시 `/build`와 새 API 기준선을 다시 확인하고 새 소유 탭에서 긴 이름을 한 번 저장한다. 저장 직후·실제GET후 재진입 새 이미지를 확인한 다음 그 실행에서 직접 생성했다고 확정한 ID만 삭제한다. 현재500/501이나 과거 ID를 정리 대상으로 재사용하지 않는다.

## 산출물

- [run.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/run.json), [target-before.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/target-before.json), [target-after.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/target-after.json), [assessment.json](/private/tmp/skill-quality-20261110/dogfood/runs/D6-retest/output/assessment.json).
- target-before와 target-after digest는 둘 다 `16f65053c53155ad4d341f379ce777667bdd97a57e6c5e7199cb27164d26d71b`이다. 계획·target에 변동이 없었고 새 현재 증거만 연결했다.
- 실행한 helper는 candidate의 `capture`2회와 `assess`1회다. 최종 판정은 complete + no_issues_observed, gaps `[]`. 이는 기록·커버리지 도구 실행이며 앱 테스트 스위트 실행이 아니다.
