# Dogfood — 프로젝트 QA D2-check

- 판정: **complete / no_issues_observed**. 필수 체크 9개를 기록했고 평가기가 보고한 gap은 없습니다. 명시 요구 위반은 관찰하지 않았습니다.
- 목표: 새 프로젝트 저장 → 실제 재조회와 재진입 → 전체 이름 읽기 → 키보드와 화면 배치 → 본인 생성 데이터 정리. 요구 기준은 현재 prompt.txt이며 앱 소스를 기준으로 기대 동작을 만들지 않았습니다.
- 대상: `http://127.0.0.1:62502/`. 시작/종료 `/build` 모두 `quality-deployment`, revision `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, backend `local-sqlite`. 특정 원하는 커밋은 제공되지 않았습니다. 이 값은 공개 엔드포인트의 관찰값이며 서버 번들의 독립적인 인증은 아닙니다.
- 세션: Chrome extension browser ID `1`, 본인 생성 tab `1893495259`. 로그인은 수행하지 않았고 계정/조직/서버 권한은 화면에 노출되지 않아 알 수 없습니다. 브라우저 버전은 도구에 노출되지 않았습니다. 모든 브라우저 조작은 이 실행자 한 명이 수행했습니다.
- 화면: 기본 CSS viewport **2504×1363**, DPR **2**. 실제 PNG는 **2504×1363**으로 도구 캡처 scale **0.5**. 이미지 바이트는 변환하지 않았습니다. host image viewer가 표시 때 2048×1115로 줄인 사실도 inspection trace에 남겼습니다. 독립 레퍼런스와 픽셀 매칭을 주장하지 않습니다.

## 체크와 증거

| 체크 / 동선 | 기대 동작의 독립 근거 | 실제 결과 | 증거 |
| --- | --- | --- | --- |
| C-01 / J-01 | prompt.txt: 새 항목 저장 | passed — 유효한 23자 이름이 저장됨 안내와 목록에 나타나고 실제 GET에서 ID 501로 확인됨. | [normal-save-keyboard.txt](evidence/normal-save-keyboard.txt), [normal-save.png](evidence/normal-save.png), [items-after-normal.json](evidence/items-after-normal.json) |
| C-02 / J-01 | prompt.txt: 재조회/재진입; 실통신은 GET/POST /api/items | passed — 네 개 유효 항목이 실제 GET에 같은 값/ID로 남으며, 다시 불러오기와 브라우저 reload 뒤 목록에 그대로 표시됨. | [items-all-saved.json](evidence/items-all-saved.json), [all-refresh.txt](evidence/all-refresh.txt), [all-reentry.txt](evidence/all-reentry.txt), [all-reentry.png](evidence/all-reentry.png) |
| C-03 / J-02 | prompt.txt: 요구: 이름은 1~200자 | passed — 1자 검=ID 502, 정확히 200자 이름=ID 503 저장 성공. GET에서 원문과 길이 확인. | [minimum-save-confirmed.txt](evidence/minimum-save-confirmed.txt), [maximum-save.txt](evidence/maximum-save.txt), [items-after-boundaries.json](evidence/items-after-boundaries.json) |
| C-04 / J-02 | prompt.txt: 요구: 이름은 1~200자 | passed — 빈 이름은 브라우저 필수 입력 오류로 차단. 201자 UI 저장 뒤 미확인 안내가 표시됐고 즉시 실제 GET에서 미생성 확인. 이후 직접 API POST 400 invalid_name 및 재조회로 거절 확인. UI 오류는 구체적인 길이를 설명하지 않음. | [blank-validation.json](evidence/blank-validation.json), [blank-submit.txt](evidence/blank-submit.txt), [overlimit-submit.txt](evidence/overlimit-submit.txt), [overlimit-submit.png](evidence/overlimit-submit.png), [items-after-boundaries.json](evidence/items-after-boundaries.json), [api-overlimit-response.json](evidence/api-overlimit-response.json), [items-all-saved.json](evidence/items-all-saved.json) |
| C-05 / J-03 | prompt.txt: 요구: 목록에서 전체를 읽을 수 있어야 함; 지정 문자열 저장 확인 | passed — 지정 문자열이 ID 504로 저장되어 재진입 뒤 목록에서 전체 내용 확인까지 한 줄로 표시됨. 200자 이름도 줄바꿈되어 끝까지 표시됨. | [required-long-save.txt](evidence/required-long-save.txt), [all-reentry.png](evidence/all-reentry.png), [reentry-metrics.json](evidence/reentry-metrics.json), [image-inspection-trace.json](evidence/image-inspection-trace.json), [items-all-saved.json](evidence/items-all-saved.json) |
| C-06 / J-04 | prompt.txt: 키보드 조작 점검 | passed — 실제 Tab으로 입력→저장→다시 불러오기→첫 삭제로 이동하여 미지원 보관을 건너뜀. 입력 Enter 저장과 재조회 Enter 동작. 보라색 포커스 테두리를 실제 이미지에서 확인. 삭제는 활성화하지 않았음. | [keyboard-tab-input.txt](evidence/keyboard-tab-input.txt), [keyboard-tab-input.png](evidence/keyboard-tab-input.png), [normal-save-keyboard.txt](evidence/normal-save-keyboard.txt), [keyboard-tab-save.txt](evidence/keyboard-tab-save.txt), [keyboard-tab-refresh.txt](evidence/keyboard-tab-refresh.txt), [keyboard-refresh-focus.png](evidence/keyboard-refresh-focus.png), [keyboard-refresh-result.txt](evidence/keyboard-refresh-result.txt), [keyboard-skips-archive.txt](evidence/keyboard-skips-archive.txt) |
| C-07 / J-03 | prompt.txt: 지원 화면 배치 점검; 명시된 모바일 지원 약속 없음 | passed — 실제 기본 데스크톱 CSS 2504×1363에서 입력·저장·재조회·보관 및 모든 목록 행이 겹치지 않고 가로 오버플로 없음. 200자 행은 640×157로 확장되며 버튼과 구분됨. 명시된 지원 범위가 없어 다른 해상도/모바일을 주장하지 않음. | [all-reentry.png](evidence/all-reentry.png), [reentry-metrics.json](evidence/reentry-metrics.json), [image-inspection-trace.json](evidence/image-inspection-trace.json) |
| C-08 / J-04 | prompt.txt: 보관 버튼 미지원 비활성이 의도 | passed — AX와 DOM에서 보관 (미지원)은 disabled=true. 실제 Tab에서도 건너뜀. 요구한 의도된 상태로 판정. | [initial-ax.txt](evidence/initial-ax.txt), [initial-metrics.json](evidence/initial-metrics.json), [keyboard-skips-archive.txt](evidence/keyboard-skips-archive.txt) |
| C-09 / J-05 | prompt.txt: 자신이 생성한 데이터만 정리; 기존 데이터 보존 | passed — 직접 생성한 ID 501~504를 정확한 행의 삭제 버튼으로 정리. reload와 실제 GET에서 기존 ID 500/이름 한 건만 유지. 시작 응답과 최종 응답의 body가 동일함. | [cleanup-plan.json](evidence/cleanup-plan.json), [cleanup-504.txt](evidence/cleanup-504.txt), [cleanup-503.txt](evidence/cleanup-503.txt), [cleanup-502.txt](evidence/cleanup-502.txt), [cleanup-501.txt](evidence/cleanup-501.txt), [cleanup-reentry.txt](evidence/cleanup-reentry.txt), [cleanup-final.png](evidence/cleanup-final.png), [items-after-cleanup.json](evidence/items-after-cleanup.json) |

## 관찰한 안내 개선점

**O-01 — 201자 이름의 안내가 입력 제한을 설명하지 않음** (`observed_once`, UI 제출 1회).

빈 이름에는 “이 입력란을 작성하세요.”가 표시됐습니다. 정확히 201자인 `D2-20261110-` + `나` 189개를 입력하고 저장했을 때에는 “저장 결과 미확인. 다시 불러오기로 확인하세요.”가 표시됐습니다. 즉시 실제 GET으로 저장되지 않았음을 확인한 다음, 같은 공개 API에 직접 POST해 **HTTP 400 / `{"error":"invalid_name"}`** 응답을 확인했고 다음 GET에도 항목은 없었습니다. 불확실한 쓰기를 그대로 반복하지 않았습니다.

이름 범위 요구는 지켜졌으므로 확정 요구 위반으로 집계하지 않았습니다. 다만 안내만 읽으면 사용자는 이름 길이를 바꿔야 한다는 사실을 알기 어렵습니다. 오류 문구의 명시 요구는 제공되지 않았으며, 원인을 소스 코드나 서버 내부 동작으로 단정하지 않습니다. 증거: [실제 UI 결과](evidence/overlimit-submit.txt), [이미지](evidence/overlimit-submit.png), [불확실한 결과 직후 GET](evidence/items-after-boundaries.json), [실제 API 응답](evidence/api-overlimit-response.json).

## 실제 통신과 데이터 정리

UI에서 이름 **23자**, **1자**, **200자**, 지정 문자열 **품질 평가를 위한 긴 프로젝트 이름 - 전체 내용 확인**을 저장했습니다. 실제 GET 응답에서 각각 ID **501, 502, 503, 504**와 원문을 확인했습니다. “다시 불러오기”와 브라우저 reload 재진입 후에도 동일하게 표시됐습니다. 브라우저 POST 요청 전문을 직접 보는 네트워크 기능은 노출되지 않았으므로 UI POST 요청 본문 캡처를 주장하지 않습니다. 실제 원격 효과는 독립된 HTTP GET으로 검증했고, 경계 거절은 직접 실제 POST로 확인했습니다. mock·응답 대체·내부 상태 주입은 사용하지 않았습니다.

[정리 계획](evidence/cleanup-plan.json)에 기록한 정확한 생성 ID를 역순 **504 → 503 → 502 → 501**으로 해당 행의 UI 삭제 버튼을 통해 정리했습니다. reload 후 화면과 실제 GET에 **ID 500 / 기존 사용자 프로젝트 - 보존 대상**만 남았습니다. 시작과 종료 GET의 body가 동일합니다. [시작 데이터](evidence/items-before.json), [정리 후 실제 데이터](evidence/items-after-cleanup.json), [정리 후 화면](evidence/cleanup-final.png).

본인이 연 탭 `1893495259`는 최종 화면 캡처 뒤 닫았습니다. 다른 탭, 브라우저 설정, viewport override, 프로세스는 변경하지 않았고 서버를 시작하거나 중지하지 않았습니다. 정리 대기 항목은 없습니다.

## 한계와 재진입

현재 기본 데스크톱 화면에서 실제 이미지와 키보드 입력을 확인했습니다. 제공된 `/build`와 화면에는 별도 지원 해상도/모바일 계약이 없어 다른 화면 크기 지원을 주장하지 않습니다. 포괄적인 접근성 감사, 브라우저 호환성/부하 테스트, 소스 코드 리뷰, 자동 앱 테스트 실행, 릴리스 승인은 수행하지 않았습니다. 콘솔/브라우저 네트워크 전문은 수집하지 않았습니다.

재진입하려면 위 URL을 열고 본인 식별 이름을 저장한 뒤 공개 GET의 반환 ID를 기록하고 재조회/reload를 확인하면 됩니다. 새로 만든 정확한 ID만 정리해야 합니다. 확정 이슈 재현을 위한 미완료 작업은 없으며, O-01의 문구 개선을 원하면 길이 제한을 사용자에게 명시하는 요구를 별도로 정할 수 있습니다.

- [실행 레코드](run.json)
- [평가 결과](assessment.json)
- [시작 대상](target-before.json) / [종료 대상](target-after.json)
- [도구 추적](evidence/tool-trace.md)
- [이미지 열람 추적](evidence/image-inspection-trace.json)
