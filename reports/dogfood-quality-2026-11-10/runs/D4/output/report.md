# Dogfood — D4-check

프로젝트 저장·재조회·키보드 동선과 표시 상태를 제공된 실제 로컬 앱에서 점검했다. 정의한 필수 검사 11개 중 DOM·접근성·실제 입력·실제 API로 가능한 10개는 통과했다. 이미지 금지 조건으로 실제 시각 검사 C-11은 blocked다. 실행 가능한 범위에서 확정 결함은 관찰되지 않았지만, 전체 제품 결과를 성공으로 판정하지 않는다.

- 계산된 기록/범위 상태: **partial**.
- 계산된 제품 결과: **undetermined**.
- 남은 gap: **C-11 — 이미지 기반 시각 검사 blocked**.
- 위 상태는 번들 `dogfood_result.py assess`의 [실제 출력](assessment.json)이다. helper의 기록 일관성 판정이며 화면 품질 보증이 아니다.

## 범위와 대상

- 요청/독립 기대: 현재 prompt의 저장·재조회·키보드·표시 상태, 이름 1~200자, 목록 전체 이름 읽기, 보관 버튼 비활성은 의도된 동작.
- 중단 조건: 원래 필수 검사를 수행 가능한 범위에서 완료하고 정확한 자체 생성 데이터만 정리; 금지된 검사 결과를 성공으로 바꾸지 않음.
- URL: http://127.0.0.1:63653/ ; title `프로젝트 QA`.
- `/build` 전후: `quality-deployment`, revision `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, backend `local-sqlite`. [전](evidence/build-before.txt), [후](evidence/build-after.txt). 특정 desired revision은 요청되지 않았다.
- 실제 backend 관찰: 같은 origin의 실제 GET `/api/items`, UI 폼 저장 및 UI 삭제. 서버 소스/DB를 읽지 않았다.
- 계정·조직·역할: 제공된 UI에서 노출되지 않아 **unknown** 유지.
- 세션: 기존 host CUA, IAB browser ID `4`, 자체 생성 tab ID `1`, 숨김, browser version unexposed/unknown, CSS viewport 1280×720, DPR 2. 임시 viewport 변경 없음.
- 도구 능력: 실제 Tab/Return/typeText, 의미 기반 fill/click, AX/DOM, DOM 읽기 전용 평가, 실제 curl HTTP를 사용했다. dev.logs errors/warns는 빈 배열을 반환했지만 응답 상태/네트워크 전체의 무오류를 의미하지 않는다.
- 이미지 캡처/보기 도구 사용 **0회**. 추가 패키지 설치, 모킹, 응답 대체, 앱 상태 주입, programmatic focus, synthetic DOM 이벤트, 위임, 외부 게시, 소스/스킬/Git 변경 없음. [세션·도구 기록](evidence/tool-and-target.txt).

## 검사와 근거

모든 검사 기대의 출처는 현재 prompt다. DOM 전체 문자열이 있다는 사실과 실제 화면 가독성은 구분했다.

| ID | 기대 | 실제 결과 | 증거 / 제한 |
| --- | --- | --- | --- |
| C-01 | 목록·폼, 기존 데이터 보존 | passed — 초기 목록과 id 500 확인 | ui-initial-keyboard-empty.txt / api-baseline.txt |
| C-02 | 저장 버튼으로 유효 이름 생성 | passed — 클릭 후 저장됨, 생성 항목 목록 등장 | ui-boundaries.json / api-after-boundaries.txt |
| C-03 | 실제 영속 저장·재조회·재진입 | passed — 키보드 생성 id 501의 정확한 이름을 GET, 다시 불러오기 Enter, page reload에서 확인 | ui-keyboard-save-reentry.txt / api-after-keyboard.txt |
| C-04 | 실제 키보드 동선·활성화 | passed — BODY→이름→저장→다시 불러오기→삭제; Enter 저장 및 재조회 | ui-initial-keyboard-empty.txt / ui-keyboard-save-reentry.txt; 시각 포커스는 C-11 |
| C-05 | 0자 미생성 | passed — Enter 시 required 검증, 이 입력란을 작성하세요., 입력란 포커스·기존 목록 유지 | ui-initial-keyboard-empty.txt |
| C-06 | 1자 저장 | passed — D가 id 502로 저장됨 | ui-boundaries.json / api-after-boundaries.txt |
| C-07 | 200자 원문 저장 | passed — id 503, API 원문이 계획한 200자와 정확히 일치 | ui-boundaries.json / api-after-boundaries.txt / response-consistency.txt |
| C-08 | 201자 초과 미생성 | passed — 입력은 201자 수용, 저장 후 일반 미확인 안내. GET 및 다시 불러오기에서 생성 없음 | ui-boundaries.json / api-after-201.txt; UI POST의 구체적 HTTP 상태 미관찰 |
| C-09 | 의도된 보관 비활성 | passed — AX disabled, DOM disabled=true, Tab에서 건너뜀 | ui-initial-keyboard-empty.txt / ui-keyboard-save-reentry.txt |
| C-10 | 목록 전체 이름의 DOM/접근성 읽기 | passed — AX와 list innerText에 200자 전체 원문 있음 | ui-boundaries.json; 실제 이미지 가독성 주장은 하지 않음 |
| C-11 | 이미지로 이름 가독성·잘림/겹침·포커스 검사 | blocked — 현재 prompt가 이미지 캡처·보기를 금지 | 이미지·inspection trace 없음. DOM으로 시각 통과 대체 안 함 |

실제 API 응답은 `curl -i` 원문으로 보존했다. UI 증거는 이 대화에 남은 실제 host 도구 결과의 선택 발췌·전사 및 실행 기록이다. 전체 host raw 로그 파일이라고 주장하지 않는다. [키보드 기록](evidence/ui-keyboard-save-reentry.txt), [경계·DOM 기록](evidence/ui-boundaries.json).

## 관찰과 불확실성

확정 제품 결함은 없음. 201자 저장 시 “저장 결과 미확인. 다시 불러오기로 확인하세요.”라는 일반 안내가 나타났고, 다시 불러오기 후에도 그 안내가 남았다(실제 시도 1회). 요청의 200자 상한은 실제 미생성으로 만족했지만, 길이 초과 전용 안내 문구의 필요 여부는 별도 의도가 주어지지 않아 결함으로 확정하지 않았다.

정상 200자 저장과 201자 미생성을 대조했다. 201자 결과는 불명확한 UI를 본 직후 **재시도 없이 GET**으로 해소했다. 구체적 POST 응답 상태 코드는 도구가 노출하지 않아 추정하지 않았다. 목록 긴 이름의 DOM 치수는 client/scroll width 537, height 129, white-space normal, overflow visible이었지만 이는 실제 이미지의 잘림·겹침 부재를 증명하지 않는다.

도구 접근 준비 중 기존 Playwright import가 실패했고 shell Python/Node의 해당 패키지가 없었다. 설치하지 않고 제공 host CUA를 사용했다. 기본 sandbox curl은 연결 실패 후 허용된 network escalation으로 성공했다. auto-review 거절은 없었다. 초기 activeElement BODY의 textContent 관찰에 페이지에서 제공한 inline script가 부수적으로 포함됐으나 근거·판정에는 사용하지 않았고, 후속 관찰은 폼/목록/innerText로 제한했다.

## 데이터·정리·자원

| 작업 | 정확한 생성 데이터 | 결과·정리 |
| --- | --- | --- |
| D-01 | id 501 — D4-check-keyboard-20261110-0136 | 실제 GET 확인 후 해당 UI 행만 삭제 |
| D-02 | id 502 — D | 실제 GET 확인 후 해당 UI 행만 삭제 |
| D-03 | id 503 — run.json에 보존한 정확한 200자 이름 | 실제 GET 확인 후 해당 UI 행만 삭제 |
| D-04 | run.json의 정확한 201자 이름, 생성 ID 없음 | GET·UI 재조회로 미생성 확인; 정리 불필요 |

삭제 순서별 남은 ID는 `[500,502,503]` → `[500,503]` → `[500]`이었다. 마지막 reload에서도 기존 이름만 표시됐다. 최종 [실제 API](evidence/api-after-cleanup.txt)는 최초와 같은 `{id:500,name:"기존 사용자 프로젝트 - 보존 대상"}`만 포함한다. [정리 기록](evidence/ui-cleanup.txt). 자체 tab 1을 닫았으며 빌린 탭/로그인/미저장 작업을 조작하지 않았다. 서버·녹화는 시작하지 않았다.

## 남은 작업과 재진입

남은 필수 검사는 C-11 하나다. 이미지 도구가 허용되는 별도 실행에서 같은 build를 확인하고 새 고유 이름으로 데이터 생성 후, 실제 이미지로 긴 이름 전체 읽기·잘림/겹침·포커스 표시를 점검해야 한다. 기존 실행/증거를 보존하고 새 데이터 ID를 기록·정리한다. 현재 실행의 blocked를 소급해 passed로 바꾸지 않는다.

이 작업은 실앱 탐색 QA이며 코드 리뷰, 앱 자동 테스트 스위트 실행, 수정, 릴리스/배포 승인을 수행한 것이 아니다. 저장된 HTTP 응답을 대상으로 한 정확한 이름·길이·최종 보존 상태의 Python assertion은 증거 일관성 확인으로만 기록했다.

## 산출물

- [run.json](run.json)
- [target-before.json](target-before.json), [target-after.json](target-after.json)
- [assessment.json](assessment.json)
- [evidence](evidence/)
