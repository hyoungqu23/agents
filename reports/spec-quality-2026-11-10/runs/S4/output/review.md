# S4-update 갱신·검토 기록

2026-11-10 작업. 현재 prompt와 지정 candidate 및 이 case documents/sources/output만 사용했다. 문서 갱신은 documents/SPEC.md와 QUESTIONS.md에만 적용했다. Git·브라우저·외부 게시·위임·앱/실서버 호출을 수행하지 않았다.

- SPEC revision 3 → 4, status blocked → ready. QUESTIONS revision 1 → 2.
- 기존 SPEC의 ready 설명은 revision 1~2를 대상으로 했고 revision 3의 수동 AC-owner/Q-010 편집을 검토한 증거가 아니므로 재사용하지 않았다. 이전 검토 본문은 SPEC §6.3의 역사로 보존했다.
- 최신 api.md v2 전체와 DEC-027 전체를 직접 읽었다. request/DESIGN/ux도 전체 재독했다. selected-reference.png는 view_image로 직접 보고 PNG 헤더의 1280×800 파일 치수를 확인했다. 실제 viewport·동작은 관찰하지 않았다.
- 변경: 200 본문을 {items,total}로, 목록은 items·개수는 total로 갱신. owner_name은 optional/null 허용 응답 필드이며 누락/null/빈 문자열→미지정, 나머지 문자열 그대로. 요청 body로 추가하지 않는다. 첫 진입 All 조회와 프로젝트 자동선택 금지를 확정했다.
- AC-1/AC-2/AC-3/AC-owner, Q-001/Q-002/Q-010, OD-owner 및 USER-EDITED 문장을 보존했다. 실패/Retry/선택 유지/같은 id 복귀/이전 성공·실패·finally 무효화 시나리오를 유지했다. 원 사용자 메모와 Q-010 추가 메모도 과거 원문으로 보존했다.
- Q-002 open→resolved, Q-010 deferred→resolved는 DEC-027 및 v2의 실제 답변을 근거로 했다. Q-010의 차단 yes는 해결 전 영향 기록이다. Q-001은 v2 배포 미확인으로 open/no 유지. Q-002의 잔여 표현 세부사항인 정확한 미선택 안내 문구는 새 Q-011 open/no로 분리했다. 초기 요청/선택 동작과 정확한 문자열을 구분했으며 미응답을 해결 처리하지 않았다.

## 새로 수행한 네 검토

| 검토 | 실제 수행 | 결과·한계 |
| --- | --- | --- |
| 구조·ID·상호 참조 | 현재 SPEC/QUESTIONS 전체와 기존 원문 대조, 동반 경로·feature identity·네 canonical AC·기존/새 Q 관계 확인. helper를 변경 후 실행하고 출력 확인 | valid, gaps [], active_blockers []. helper는 구조와 기록 존재만 검사한다. 시각적 표 검토에서 추가 source/flow 행 앞 빈 줄을 발견해 두 번째 pass에서 연결했다 |
| 원자료·권위·판본 | v2 및 DEC-027의 명시적 확정·대체 범위를 규칙·역수용 표와 대조하고 나머지 제공 원자료 및 이미지를 직접 확인 | v2 필드/방향/fallback, All/자동선택, 디자인·700px·label/focus 반영. 원 v1 파일은 별도 제공되지 않아 읽지 못했다. 변경 없는 Project 세 필드·503 shape는 기존 SPEC 기록과 v2의 동일성 명시를 근거로 유지했다 |
| 화면·정책·API·AC 정합성 | 초기/필터/선택/empty/실패/Retry/응답 역전/담당자 경로를 §3→§4→§5→§6.1로 대조 | 현재 매핑에서 items 목록·total 개수 일치. 빈 성공 fixture는 {items:[],total:0}. 예전 배열 본문/length 매핑은 현재 규칙에서 제거했고 이전 검토의 과거 원문에만 유지. 앱 실행은 미수행 |
| AC별 구현 내용 재구성 | 별도 독자 없이 현재 문서·명시 원자료를 다시 읽고 아래 네 AC의 actor/초기 상태/trigger/request/success/failure/recovery 재구성 | 선언 범위에 새 차단 가정 미발견. 자기 검토이며 독립 검증/정확성 인증/실행 테스트가 아니다 |

## AC별 재구성

| AC | 사용자·초기 상태 → 행동 | 요청·성공 UI | 실패·회복·관찰할 내용 |
| --- | --- | --- | --- |
| AC-1 | 목록 사용자 첫 진입 → All 조회, 이후 네 Status 명시 선택 | GET status=all/active/archived/paused, 최신 200 items 목록 및 total 개수. items 2개/total 7 fixture에서 7 표시 검증 가능 | 최신 실패는 AC-3 경로, 이전 결과는 현재 필터 결과로 확정하지 않음. 실제 실행 미수행 |
| AC-2 | 첫 진입 미선택 → P 선택 → 필터 밖 → empty → P 복귀 | 최초 자동선택 없음. 순수 FE P 선택으로 name 표시. 필터 GET 후에도 독립 선택 객체 유지, 같은 id 행 표시 복구 | loading/error/Retry/empty에도 P 유지. {items:[],total:0}은 오류 없이 결과 없음·0. 최초 안내 문자열만 Q-011 |
| AC-3 | P 선택·현재 필터 조회 → 503 → Retry, A 뒤 B 요청 시작 | Retry 클릭 당시 current status GET, 새 최신 요청 기준 items/total 또는 실패 반영 | 503 오류/Retry와 빈 성공 구별. A성공/B실패, A실패/B성공 역순 및 B 대기 중 A finally 무효화. P 유지. 동일 필터 Retry에도 적용 |
| AC-owner | 최신 성공 items → 각 owner_name 표시 | 추가 API 없이 응답 필드 매핑. 누락/null/빈 문자열은 미지정. 일반/공백 문자열은 그대로 | fallback을 이유로 행을 제거하거나 조회 실패로 바꾸지 않음. 응답 필드를 요청 body로 보내지 않음. 실패·최신성은 공통 조회 규칙 유지 |

## helper 실행

작업 디렉터리와 무관한 절대 경로로 아래 명령을 두 번 실행했다. `-B`는 candidate 내부 bytecode 파일 생성을 막는다. 두 실행 모두 exit code 0이었다. 첫 출력은 spec-check-pass1.json, 최종은 spec-check-current.json이다. 기존 documents/spec-check.json은 덮어쓰지 않았다.

```sh
python3 -B /private/tmp/skill-quality-20261110/spec/candidate/scripts/spec_check.py --spec /private/tmp/skill-quality-20261110/spec/runs/S4-update/documents/SPEC.md --questions /private/tmp/skill-quality-20261110/spec/runs/S4-update/documents/QUESTIONS.md
```

첫 pass는 내용 갱신·네 자기 검토, 두 번째 pass는 source/flow 표의 행 연결 보정과 의미 영향 없음 확인이다. 추가 self-revision은 하지 않았다. 최종 helper의 해시는 최종 문서 바이트와 대조한다. 이것은 내용 진위나 앱/서버 동작 검증을 대신하지 않는다.

## 보존과 미확인 범위

원자료 여섯 파일과 기존 documents/spec-check.json의 작업 전후 SHA-256 동일 여부는 preservation-check.json에 기록했다. 두 문서의 작업 전 원문은 *.before, 실제 변경은 *.diff에 기록했다. 보존 audit는 ID·원문·기존 질문 이력 및 이전 검토 본문 유지를 확인한다.

제공된 현재 원자료에서 읽지 않은 파일은 없다. 별도 원 v1 파일, OpenAPI/생성 타입, 실제 앱 코드·오류 컴포넌트·초기화 코드, 실서버 배포 버전은 제공되지 않았고 읽거나 검증하지 않았다. 현재 ready는 선언된 네 AC의 문서 준비 판정이다. 네 AC 모두 v2 제어 응답으로 독립 개발·후속 검증할 수 있으나 실제 구현·테스트·게시를 수행했다는 의미는 아니다.
