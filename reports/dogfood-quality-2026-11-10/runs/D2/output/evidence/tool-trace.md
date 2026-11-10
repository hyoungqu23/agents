# 실제 도구 호출 추적

이 파일은 실행 도구 호출의 인수와 관찰 결과를 요약하며, 연결된 AX/JSON/PNG 파일은 각 도구가 반환한 실제 값/바이트입니다. 스크린샷을 합성하거나 재현 UI를 만들지 않았습니다.

1. `mcp__cua_repl.js`: createBrowserTab("chrome", "http://127.0.0.1:62502/", {sessionName:"🔎 Dogfood D2"}) → tab 1893495259, browser 1. initial AX/PNG/DOM metrics 저장.
2. `exec_command`: 일반 sandbox의 urllib GET은 `PermissionError: [Errno 1] Operation not permitted`. 허용된 로컬 API 읽기를 require_escalated로 재실행했고 GET /build와 /api/items HTTP 200. 응답은 build-before.json, items-before.json에 기록.
3. bundled `dogfood_result.py capture` → target-before.json.
4. `mcp__cua_repl.js`: pressKey(null,"Tab"), getAXState, getScreenshot → input focus. Return on blank → 필수 입력 validationMessage. native typeText exact normal name, Return → 저장됨/목록. 실제 API GET → ID 501.
5. `mcp__cua_repl.js`: Tab save → Tab refresh → Return refresh → Tab first delete. disabled archive skipped; actual focus PNG 저장. 삭제를 키보드로 실행하지 않음.
6. `mcp__cua_repl.js`: reload → fresh AX. 1자 입력 뒤 첫 click은 입력란을 클릭했으므로 목록 변화 없음. fresh AX에 근거한 저장 버튼 click으로 실제 생성. 200자 setValue + Save → 저장됨. 201자 setValue + Save → 저장 결과 미확인. actual GET → 502/503 존재, 201자 없음.
7. `mcp__cua_repl.js`: 지정 긴 문자열 setValue + Save → 저장됨/목록. 실제 공개 POST 201자 → HTTP 400 invalid_name. GET → ID 504 포함한 전체 유효 저장 항목.
8. `mcp__cua_repl.js`: getBrowser({id:"1"}) 및 viewport capability documentation 읽기. viewport set/reset은 호출하지 않음.
9. `mcp__cua_repl.js`: 다시 불러오기 click → reload → fresh AX, screenshot PNG, read-only DOM dimensions → 유효 네 항목 유지.
10. `functions.exec -> tools.view_image`: all-reentry.png 실제 파일 열람. source 2504×1363, high display 2048×1115; image delivered. inspection-trace에 인수/실제 결과/관찰을 기록.
11. `mcp__cua_repl.js`: fresh AX에 근거해 자기 항목의 삭제 버튼을 504/503/502/501 순으로 클릭, 매번 getAXState. reload, final screenshot → 보존 대상만 남음. owned tab.close() 완료, completion_summary 제출.
12. `exec_command`: 실제 GET /api/items와 /build → ID 500만 남고 시작 body 동일, build/revision/backend 동일. bundled capture after + assess → complete, no_issues_observed, gaps [].

도구에 노출되지 않은 브라우저 버전, 서버 인증 역할, 브라우저 POST 네트워크 전문은 수집/검증했다고 주장하지 않습니다.
