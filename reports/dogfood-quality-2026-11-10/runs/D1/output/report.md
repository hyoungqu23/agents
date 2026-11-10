# Dogfood — D1 journey

기록·커버리지 판정: **complete**. 제품 판정: **issues_found**. 필수 체크 11개 중 10개 통과, 1개 실패, 미실행 필수 체크 0개. 이 판정은 번들 recorder가 파일·기록의 일관성을 검사한 결과이며 제품 품질 승인이나 이미지 판정의 자동 인증이 아니다.

사용자 목표는 기존 항목을 보존하면서 실제 프로젝트 저장 → 재조회 → 재진입 → 삭제를 검증하고, 1~200자 이름·전체 표시·키보드 동선·응답 유실 회복을 확인하는 것이었다. 원래 필수 범위를 유지했고 생성 데이터 정리와 증거 기록을 중단 조건으로 삼았다.

## 대상과 도구

- URL: http://127.0.0.1:61464/. /build는 시작과 종료에 `quality-deployment`, revision `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, backend `local-sqlite`를 반환했다. 사용자 지정 revision은 없었으며 소스/DB를 읽지 않았다.
- 로그인 화면 없는 익명 UI만 검증했다. 실제 API는 소유 탭으로 GET /api/items에 접속해 받은 JSON으로 확인했다. POST/DELETE는 앱 UI에서 실행하고 독립 GET 및 재진입으로 실제 저장·삭제 결과를 검증했다.
- 주 도구: `mcp__cua_repl.js`, Chrome extension browser 2, profile aents.co, 새로 만든 own tab 1893495255. 버전은 도구가 노출하지 않았다. iab 생성 시도는 unavailable로 실패했다. Chrome 생성은 성공했으나 최초 변수 대입 오류 후 생성한 동일 탭을 id로 재연결했다.
- 시작 전 inventory에는 다른 탭 메타데이터가 도구 결과에 포함되었다. 다른 탭의 본문은 열거나 저장하지 않았다. 기존 탭/세션은 변경하지 않았고 소유 탭만 마지막에 종료했다.
- 실제 이미지: getScreenshot JPEG bytes를 저장하고 `nodeRepl.emitImage`로 디코딩된 이미지를 확인했다. `tools.view_image`로 저장된 재진입 이미지를 추가 열람했다. 원본 2504×1363, CSS viewport 2504×1363, DPR 2, capture scale 1. 보조 viewer만 2048×1115로 표시했으며 원본은 변환·리사이즈하지 않았다.

## 체크와 증거

| ID | 기대와 근거 | 실제 결과 | 주요 증거 |
| --- | --- | --- | --- |
| C-01 | 정상 저장값이 실제 API와 재진입에서 동일하다 — prompt.txt | **passed**: 지정 이름 UI Enter 저장→저장됨→다시 불러오기 Enter→실제 GET id501 name29자 원문 일치→/ 재진입 확인. POST 응답 자체의 HTTP 상세는 미수집. | [05-api-after-long.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/05-api-after-long.txt), [06-reentry-long.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/06-reentry-long.txt) |
| C-02 | 생성한 프로젝트를 UI에서 삭제하면 API와 재진입에서 제거된다 — prompt.txt | **passed**: id501 UI 삭제 Enter 후 즉시 AX는 미변경이었으나 재시도 없이 실제 GET과 재진입에서 제거됨 확인. 다른 생성 항목도 UI 삭제 후 실제 GET과 재진입에서 제거 확인. | [24-api-after-delete-501.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/24-api-after-delete-501.txt), [25-reentry-after-delete-501.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/25-reentry-after-delete-501.txt), [29-clean-api.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/29-clean-api.txt) |
| C-03 | 지정된 긴 프로젝트 이름을 목록에서 전체 읽을 수 있다 — prompt.txt | **failed**: 저장 직후와 API 확인 후 재진입 이미지에서 이름이 짧은 고정 영역에서 잘려 전체 이름을 읽을 수 없음. AX/API에는 원문 전체 있음. 서로 다른 이름인 기존 항목도 잘림. | [03-long-name.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/03-long-name.jpg), [07-reentry-clipping.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/07-reentry-clipping.jpg), [03-image-inspection-trace.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/03-image-inspection-trace.txt) |
| C-04 | 실제 Tab/Shift+Tab/Enter로 저장·새로고침·삭제에 접근하고 초점을 볼 수 있다 — prompt.txt | **passed**: 실제 locator.press Tab으로 입력→저장→다시 불러오기→기존 삭제→내 삭제 이동, Shift+Tab으로 입력 복귀, Enter로 저장·재조회·내 항목 삭제. 보관은 건너뛰고 저장/내 삭제 초점 링 이미지 확인. 각 locator.press는 시작 요소를 포커스함을 공개. | [04-keyboard-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/04-keyboard-save.txt), [04-delete-focus.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/04-delete-focus.jpg), [23-delete-501-keyboard.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/23-delete-501-keyboard.txt) |
| C-05 | 빈 이름(0자)을 저장하지 않는다 — prompt.txt | **passed**: 빈 입력에서 Enter 시 브라우저 required 검증 이 입력란을 작성하세요. 입력 초점 유지, 항목 추가 없음. | [02-keyboard-empty.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/02-keyboard-empty.txt) |
| C-06 | 1자 이름을 정확히 저장·재조회할 수 있다 — prompt.txt | **passed**: 가 1자 UI 저장됨, 실제 GET id502 name 가 length1, / 재진입 목록 동일. | [10-api-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/10-api-boundaries.txt), [11-reentry-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/11-reentry-boundaries.txt) |
| C-07 | 200자 이름을 정확히 저장·재조회할 수 있다 — prompt.txt | **passed**: 경×200 UI 저장됨, 실제 GET id503 name200자 원문 일치, / 재진입 목록 동일. 전체 표시 문제는C-03에서 분리. | [10-api-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/10-api-boundaries.txt), [11-reentry-boundaries.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/11-reentry-boundaries.txt) |
| C-08 | 201자 이름을 제한하여 200자 초과값이 저장되지 않는다 — prompt.txt | **passed**: 실제 문자 키 입력으로201자 도달, 저장1회 후 결과 미확인 메시지. 재전송 없이 다시 불러오기와 실제 GET에서 초×201 미저장 확인. 명시적인 길이 안내가 아닌 점은 관찰만 남김. | [14-201-input-complete.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/14-201-input-complete.txt), [15-201-save-outcome.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/15-201-save-outcome.txt), [17-api-after-201.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/17-api-after-201.txt) |
| C-09 | lost-response 저장 응답 유실 시 재전송 전에 실제 목록/API를 확인하고 중복 저장하지 않는다 — prompt.txt | **passed**: lost-response 저장1회 후 결과 미확인 표시. 재전송 없이 목록 재조회→실제 GET에서 id504 한 개→재진입 확인. 쓰기 전달 여부를 해소했고 중복 없음. 정확한 응답 손실의 HTTP 원인은 미수집. | [18-lost-response-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/18-lost-response-save.txt), [19-lost-response-list-requery.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/19-lost-response-list-requery.txt), [20-api-lost-response.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/20-api-lost-response.txt), [21-reentry-lost-response.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/21-reentry-lost-response.txt) |
| C-10 | 보관은 명시적 미지원이며 비활성화되어 있다 — prompt.txt | **passed**: 보관 (미지원)은 AX disabled이고 회색 비활성 UI. Tab은 보관을 건너뛰어 첫 삭제로 이동. 의도한 미지원이므로 결함 처리하지 않음. | [04-keyboard-save.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/04-keyboard-save.txt), [03-long-name.jpg](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/03-long-name.jpg) |
| C-11 | 기존 id 500은 보존하고 이번 실행의 정확한 생성 항목만 정리한다 — prompt.txt | **passed**: 자신이 생성한501~504만 정확한 rendered data-id로 UI 삭제. 최종 GET과 재진입에서 기존500 이름 원문 보존, 새 항목 없음. 소유 탭만 종료. | [29-clean-api.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/29-clean-api.txt), [31-clean-reentry.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/31-clean-reentry.txt), [33-cleanup-tool-trace.txt](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/33-cleanup-tool-trace.txt) |

## I-01 — 목록에서 긴 이름 전체를 읽을 수 없음

- 분류: **reproduced**, 실제 관찰 2회(저장 직후 및 API 확인 후 재진입). C-03 실패.
- 독립 기대: 이름은 1~200자이고 목록에서 전체를 읽을 수 있어야 한다는 사용자 요구. 지정 이름 `실제 사용자 동선 검증을 위한 아주 긴 프로젝트 이름`은 29자다.
- 재현: / 접속 → 지정 이름 입력 → Tab으로 저장 이동 → Enter 저장 → 목록 이미지 확인 → 실제 /api/items에서 id 501 원문 확인 → / 재진입 → 목록 이미지 재확인.
- 실제: 접근성 텍스트와 API는 이름 원문 전체를 제공하지만 실제 목록 이미지는 앞부분만 보여 주고 나머지가 잘린다. 기존 긴 항목도 잘렸다. 짧은 1자 이름은 대조 입력으로 저장됐다.
- 영향: 목록에서 프로젝트 전체 이름을 읽거나 구별하기 어렵다. 저장값 자체는 정상이다. 소스 위치와 근본 원인은 확인하지 않았다.

![재진입 후 긴 이름 잘림](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/07-reentry-clipping.jpg)

## 데이터와 정리

| 작업 | 실제 생성 id / 값 | 최종 상태 |
| --- | --- | --- |
| 정상 저장 | 501 / 지정 29자 이름 | UI Enter 삭제, 실제 GET 및 재진입에서 없음 |
| 최소 경계 | 502 / 가 (1자) | UI 삭제, 최종 GET 및 재진입에서 없음 |
| 최대 경계 | 503 / 경×200 | UI 삭제, 최종 GET 및 재진입에서 없음 |
| 응답 유실 | 504 / lost-response | 1회 저장 후 미확인 메시지. 재전송 없이 목록·API·재진입에서 한 개 확인 후 UI 삭제 |
| 초과 경계 | 생성 없음 / 초×201 | 저장 1회 후 미확인 메시지. 목록 및 실제 API에 없음. 재전송 없음 |
| 보존 대상 | 500 / 기존 사용자 프로젝트 - 보존 대상 | 시작과 최종 GET의 id·이름 동일. 삭제 동작 없음 |

201자 입력 중 sequential 입력 도구가 두 번 5초 제한에 걸렸고, 각 실패 후 실제 길이 84/167을 확인한 다음 남은 문자만 입력해 201자에 도달했다. 이는 입력 도구 한계이며 제품 결함으로 판정하지 않았다. 201자 저장 메시지는 길이 오류를 구체적으로 설명하지 않았다는 관찰을 남기되, 별도 AC 없는 오류 문구 결함으로 확정하지 않았다.

초기 501 삭제의 즉시 AX는 바뀌지 않았다. 재시도하지 않고 실제 GET을 확인해 이미 삭제됐음을 확정했다. 모든 쓰기 전달 불확실성은 재전송 전에 재조회로 해소했다. 마지막 API에는 id 500 한 개만 남았고 / 재진입 이미지로도 확인했다. 서버·녹화는 시작하지 않았다.

![정리 후 기존 항목만 보존](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/evidence/32-cleaned.jpg)

## 한계와 재진입

- 브라우저 네트워크 검사 API가 없어 원시 POST/DELETE 요청·응답 상태 코드·타이밍은 수집하지 못했다. 응답 유실의 HTTP 원인을 단정하지 않는다. 실제 UI 쓰기 뒤 독립 GET HTTP API와 재진입으로 영속 결과는 확인했다. 터미널 curl은 연결 실패로 사용할 수 없었다.
- 키보드 조작은 브라우저 locator.press와 실제 Tab/Shift+Tab/Enter를 사용했다. locator는 시작 요소를 포커스한다. 네이티브 OS 연속 키보드·IME 입력은 검증하지 않았다.
- 현재 데스크톱 viewport와 익명 역할만 포함한다. 다른 화면 크기·모바일·권한·브라우저·언어는 약속된 범위가 아니었다. 보관은 명시적 미지원이므로 정상 비활성 상태로 판정했다.
- 실제 코드 리뷰, 앱 자동화 테스트 스위트, 성능·보안 검사, 릴리즈 승인, 외부 게시, 커밋·푸시는 수행하지 않았다. 소스·DB·다른 사례·oracles·채점 코드를 읽거나 수정하지 않았고 패키지 설치·mock·내부 상태 주입·위임도 하지 않았다.
- 재검증하려면 /build를 다시 확인하고 새 소유 탭에서 지정 이름을 한 번 저장한다. 목록 이미지의 전체 표시를 점검하고 GET /api/items 및 재진입으로 원문을 대조한 뒤 새로 생성한 정확한 id만 삭제한다. 기존 id 500은 보존한다.

## 산출물

- [run.json](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/run.json), [target-before.json](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/target-before.json), [target-after.json](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/target-after.json), [assessment.json](/private/tmp/skill-quality-20261110/dogfood/runs/D1-journey/output/assessment.json)
- evidence/에는 실제 브라우저 반환 AX/API JSON 텍스트, 이미지 원본, 실제 사용 도구/이미지 열람 기록, 정리 결과를 보존했다.
- 번들 `dogfood_result.py capture`(시작·종료) 및 `assess` 실행. 최종 assess exit 0, complete + issues_found, gaps []. 앱 테스트 스위트 실행과는 다르다.
