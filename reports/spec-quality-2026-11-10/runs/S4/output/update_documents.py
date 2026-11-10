from pathlib import Path
base=Path('/private/tmp/skill-quality-20261110/spec/runs/S4-update')
spec_path=base/'documents/SPEC.md'
q_path=base/'documents/QUESTIONS.md'
s=spec_path.read_text()
old_review=s[s.index('### 6.2 명세 검토 결과'):s.index('\n사용자 추가 메모:')]

def replace(old,new):
    global s
    if old not in s: raise ValueError('Missing exact patch: '+old[:140])
    s=s.replace(old,new,1)

replace('revision: 3','revision: 4')
replace('status: blocked','status: ready')
replace('- 적용 범위·대상 환경: 프로젝트 목록의 읽기 전용 FE 동작. `api.md`의 확정 Target contract v1을 기준으로 한다. 앱·서버의 실행 환경과 배포 버전은 확인하지 않았다.', '- 적용 범위·대상 환경: 프로젝트 목록의 읽기 전용 FE 동작과 목록의 담당자 표시(AC-owner). `api.md`의 확정 Target contract v2 및 DEC-027을 기준으로 한다. 앱·서버의 실행 환경과 배포 버전은 확인하지 않았다.')
replace('- 상태 이유: 네 가지 자기 검토를 수행했고 AC-1~AC-3의 명세에 활성 차단 질문이 없다. Target contract v1 기준 문서 준비 완료(ready)이며, 실서버 배포·앱 실행 검증은 포함하지 않는다.', '- 상태 이유: 현재 SPEC revision 4와 QUESTIONS revision 2를 대상으로 네 가지 자기 검토를 새로 수행했다(§6.2). AC-1/AC-2/AC-3/AC-owner에 활성 차단 질문이 없어 Target contract v2 기준 문서 준비 상태는 ready이다. 기존 판정·파일명은 이번 판정의 근거로 재사용하지 않았다. 실서버 배포·앱 실행 검증은 포함하지 않는다.')
replace('- 미결 목록: [QUESTIONS.md](./QUESTIONS.md). 활성 차단 질문은 없다. Q-001은 배포 확인, Q-002는 기존 초기 진입 관례 확인으로 문서 준비의 차단 조건이 아니다.', '- 미결 목록: [QUESTIONS.md](./QUESTIONS.md). 활성 차단 질문은 없다. Q-002/Q-010은 DEC-027로 해결했으며 Q-001(배포 확인), Q-011(미선택 패널의 정확한 문구)은 비차단 미결로 남는다.')
replace('- 독립 개발 가능 범위: AC-1~AC-3 전체를 Target contract v1의 제어 가능한 응답으로 구현·검증할 수 있다. 준비 상태는 구현·게시 권한이나 실제 앱의 동작 보증을 뜻하지 않는다.', '- 독립 개발 가능 범위: AC-1/AC-2/AC-3/AC-owner 전체를 Target contract v2의 제어 가능한 응답으로 구현·검증할 수 있다. 첫 All 조회와 자동선택 금지도 포함한다. 준비 상태는 구현·게시 권한이나 실제 앱의 동작 보증을 뜻하지 않는다.')
replace('- 포함 범위: All/Active/Archived/Paused 선택, 선택 status의 API 요청·응답·개수 표시, 프로젝트 이름을 보여 주는 선택 패널, 동일 프로젝트가 목록에 돌아왔을 때 선택 표시 복구, 성공한 빈 결과와 오류 구분, 현재 필터 Retry, 최신 요청만 화면에 반영하는 처리.', '- 포함 범위: 첫 진입 All 조회·프로젝트 자동선택 금지, All/Active/Archived/Paused 선택, 선택 status의 API items 목록·total 개수 표시, 목록의 담당자 표시, 프로젝트 이름을 보여 주는 선택 패널, 동일 프로젝트가 목록에 돌아왔을 때 선택 표시 복구, 성공한 빈 결과와 오류 구분, 현재 필터 Retry, 최신 요청만 화면에 반영하는 처리.')
replace('`request.md:5`, `api.md:2`가 명시한 제외이며','`request.md:5`의 명시적 제외를 유지하며')
replace('| SRC-002 | [api.md](../sources/api.md):1–2 | Target contract v1; SHA-256 앞 16자 `e88847fcef6fb5f8`; 실제 배포 상태 미확인 | 파일 전체 직접 읽음 | 이번 기능의 확정 요청·응답 계약; 배포 증거는 아님 |','| SRC-002 | [api.md](../sources/api.md):1–2 | Target contract v2; SHA-256 앞 16자 `ad6418aa051ed61cc`; 실제 배포 상태 미확인 | 현재 파일 전체 직접 읽음 | 확정 계약. v1의 배열 본문/length 개수를 items/total로 대체하고 owner_name 응답 필드를 추가. Project.id/name/status와 503·Retry·최신성은 기존과 동일하다고 명시; 배포 증거는 아님 |')
replace('\n### 2.2 확정된 결정과 구현 재량', '\n| SRC-006 | [update-decision.md](../sources/update-decision.md):1–4; DEC-027, Q-002, Q-010/OD-owner | 2026-11-10 제품 책임자 확정 답변; SHA-256 앞 16자 `75a9034a67a080785` | 파일 전체 직접 읽음 | 첫 All 조회·자동선택 금지와 담당자 fallback 확정. 기존 ID·시나리오·USER-EDITED 보존 지시 |\n\n원 v1 API 파일은 별도로 제공되지 않았다. 변경되지 않은 Project의 세 필드 및 503 shape는 이번에 다시 읽은 기존 SPEC revision 3 §5.2의 계약 기술과 SRC-002의 “기존과 동일”을 함께 근거로 유지한다. 원 v1 파일을 이번에 직접 확인했다는 뜻은 아니다.\n\n### 2.2 확정된 결정과 구현 재량')
replace('| AC-1 | Status의 네 선택 값에 해당하는 실제 API 배열과 그 길이를 표시한다. | SRC-001:2, SRC-002:2 | §3~§5, AC-1 |','| AC-1 | Status의 네 선택 값에 해당하는 실제 API 응답의 items를 목록으로, total을 개수로 표시한다. items.length를 개수로 사용하지 않는다. | SRC-001:2, SRC-002:2 v2가 기존 v1 본문/개수 매핑을 대체 | §3~§5, AC-1 |')
replace('| request.md:5 / api.md:2 | 읽기 전용이다. 저장·보관 동작 및 추가 쓰기 API·권한 정책을 도입하지 않는다. | SRC-001, SRC-002의 명시적 범위 | §1, §5 |', '| request.md:5 | 읽기 전용이다. 저장·보관 동작 및 추가 쓰기 API·권한 정책을 도입하지 않는다. | SRC-001의 명시적 범위를 유지 | §1, §5 |\n| DEC-027 / Q-002 | 첫 진입은 기존 All 조회를 유지하고 프로젝트를 자동선택하지 않는다. | SRC-006:1–2의 확정 답변. 초기 동작 미확정 상태를 대체 | §3.2, §4, §5.1, AC-1/AC-2 |\n| DEC-027 / Q-010 / OD-owner / AC-owner | 목록의 owner_name 누락/null/빈 문자열은 미지정으로, 그 외 문자열은 그대로 표시한다. owner_name은 응답 필드이며 요청 body가 아니다. | 기존 사용자 추가 AC-owner와 SRC-006:3, SRC-002:2. Q-010 보류를 실제 답변으로 해결 | §3.2, §4, §5.2, AC-owner |')
replace('- 이미지의 All·Tide는 참고 화면의 상태이다. 초기 필터 기본값·자동선택·미선택 패널 문구를 이 이미지로 확정하지 않는다. 초기 진입 관례 확인은 Q-002이며, 어느 초기값을 쓰더라도 선택된 Status와 요청 값·결과·개수는 일치해야 한다.', '- 이미지의 All·Tide는 참고 화면의 상태이다. 첫 All 조회·자동선택 금지는 이미지 추론이 아니라 DEC-027의 확정 답변으로 적용한다(Q-002 해결). 최초 패널은 프로젝트 미선택 상태이고 Tide를 자동으로 표시하지 않는다. 미선택 패널의 정확한 문구는 Q-011로 분리했으며, 표시 중 Status와 query·items 결과·total 개수는 일치해야 한다.')
replace('| api.md:2 — GET/query enum, Project[]와 non-null 필드, 503/error, 배포 미확인 | §5 전체; Q-001 | 해당 없음 |', '| api.md:2 v2 — GET/query enum, 200 items/total 필수·non-null, 개수는 total, 기존 Project 세 필드·503/Retry/최신성 유지 | §3.2, §4, §5 전체, AC-1/AC-2/AC-3; 배포 미확인 Q-001 | 해당 없음 |\n| api.md:2 / update-decision.md:3 — owner_name은 optional/null 허용 응답 필드, 누락/null/빈 문자열→미지정, 그 외 원문 유지 | §2.2, §3.2, §4, §5.2, AC-owner; Q-010 해결·OD-owner 보존 | 해당 없음 |')
replace('| 이미지에서 초기 진입·미선택 상태·숨은 상호작용은 관찰되지 않음 | §2.2, Q-002 | 최초 기본값·자동선택 정책을 새로 확정하지 않음 |', '| update-decision.md:2 — 첫 All 조회 유지, 자동 프로젝트 선택 금지 | §2.2, §3.2, §4, §5.1, AC-1/AC-2; Q-002 해결 | 해당 없음 |\n| update-decision.md:4 — AC/Q/OD 및 사용자 편집·실패/Retry/선택 유지 보존 | AC-1/AC-2/AC-3/AC-owner, QUESTIONS 이력, §1의 USER-EDITED 원문, §6.3 이전 검토 보존 | 해당 없음 |\n| 이미지에서 미선택 패널 문구·숨은 상호작용은 관찰되지 않음 | §2.2, §3.1, Q-011 | 초기 동작은 DEC-027로 정하되 정확한 미선택 문구는 이미지에서 추정하지 않음 |')
replace('초기 상태 Q-002 |', '초기 동작은 DEC-027, 미선택 문구 Q-011. 담당자 필드는 이 이미지에서 관찰되지 않았고 별도 AC-owner/DEC-027로 추가 |')
replace('| Status 조회 — AC-1 |', '| 첫 진입 — AC-1/AC-2 | 기존 목록 화면에 처음 진입, 프로젝트 미선택 | 기존 All 조회를 실행 | Status All, GET status=all. 최신 성공 items를 목록으로, total을 개수로 표시. 프로젝트를 자동선택하지 않고 패널은 미선택 상태 | loading/empty/error에서도 자동선택하지 않음. 실패는 AC-3의 오류/현재 필터 Retry로 회복 | SRC-006:2, SRC-002:2, SRC-004:1; 정확한 미선택 문구 Q-011 |\n| Status 조회 — AC-1 |')
replace('최신 요청의 200 배열을 목록에 표시하고 개수는 배열 길이', '최신 요청의 200 본문 items를 목록에 표시하고 개수는 total')
replace('최신 요청이 200 + [] 반환 | 성공한 결과 없음 표시, 개수 0.', '최신 요청이 200 + {items:[], total:0} 반환 | 성공한 결과 없음 표시, 개수는 total인 0.')
replace('\n선택 유지 범위는', '\n| 담당자 표시 — AC-owner | 최신 성공 items로 목록을 표시 | 각 Project의 응답 owner_name을 읽음 | 누락/null/빈 문자열은 미지정. 그 외 문자열은 공백을 trim하거나 대소문자를 바꾸지 않고 원문 그대로 표시 | 순수 응답→FE 표시이며 요청 body·쓰기 API를 추가하지 않음. 최신 성공 목록 교체 시 해당 items의 담당자 표시 | 기존 AC-owner, SRC-002:2, SRC-006:3 |\n\n선택 유지 범위는')
replace('제공된 네 enum 값만 요청. 초기 진입 기본값은 Q-002', '제공된 네 enum 값만 요청. 첫 진입은 All, 자동 프로젝트 선택 없음(DEC-027)')
replace('성공 시 API 배열의 프로젝트 이름과 상태를 행에 표시. 개수는 실제 응답 길이', '성공 시 응답 items의 프로젝트 이름·상태·담당자를 행에 표시. 개수는 응답 total')
replace('빈 배열은 0 및 결과 없음.', 'items가 []이면 결과 없음, 개수는 항상 total; {items:[], total:0}은 0.')
replace('| 선택 패널·선택 표시 — AC-2/AC-3 |', '| 담당자 — AC-owner | 목록의 owner_name 표시 | 최신 성공 응답의 각 프로젝트에 적용; 편집 입력 없음 | 누락/null/빈 문자열→미지정. 그 외 string은 원문 그대로; 공백만 있는 문자열도 임의 trim/fallback하지 않음 | 응답 fallback은 조회 성공을 오류로 만들거나 프로젝트를 제거하지 않음. owner_name을 요청 body로 보내지 않음 | SRC-002:2, SRC-006:3; Q-010 해결 |\n| 선택 패널·선택 표시 — AC-2/AC-3 |')
replace('- 초기 미선택 상태의 문구와 앱 진입 기본값은 원자료에 없다(Q-002). 정적 이미지의 Tide 선택을 자동선택 요구로 해석하지 않는다.', '- 초기 진입은 All 조회이며 자동 프로젝트 선택은 하지 않는다(DEC-027, Q-002 해결). 최초 패널은 미선택 상태이고 이름을 임의로 채우지 않는다. 정확한 미선택 문구는 미확인(Q-011)이며 선택 후 이름 표시 계약을 바꾸지 않는다.')
replace('| Status 변경 — AC-1/AC-2/AC-3 |', '| 첫 진입 — AC-1/AC-2 | 기존 목록 화면의 첫 진입 경로 | GET `/api/projects`, operation ID 제공 없음 | query status=all. body 없음; owner_name은 요청 필드 아님 | 200: {items:Project[], total:number}; 503: {error:string} | items 목록·total 개수, 자동선택 없음. loading/empty/error 구분, 최신 요청만 반영 | SRC-006:2, SRC-002:1–2 v2. 실제 배포 미확인 Q-001 |\n| Status 변경 — AC-1/AC-2/AC-3 |')
replace('200: Project[]; 503: {error:string} | 최신 요청 200이면 배열·길이, []면 성공 empty. 최신 503이면 오류/Retry. 선택 객체 유지 | SRC-002:1–2, Target contract v1.', '200: {items:Project[], total:number}; 503: {error:string} | 최신 요청 200이면 items 목록·total 개수, items=[]면 성공 empty. 최신 503이면 오류/Retry. 선택 객체 유지 | SRC-002:1–2, Target contract v2.')
replace('최초 화면 진입 호출 시점은 원자료에 별도 정의가 없다(Q-002). 초기 결과를 조회하는 기존 진입 경로를 사용할 때도 표시 중인 Status와 query가 일치해야 한다.', '최초 화면 진입은 기존 All 조회를 유지하며 자동 프로젝트 선택을 하지 않는다(SRC-006:2, Q-002 해결). 표시 중 Status와 query가 일치해야 한다.')
replace('| 응답 200 본문 | Project[]; 배열 전체. null 본문 지원은 명시되지 않음 | 목록은 반환 배열, 개수는 length | []는 성공 empty 및 0. 실패를 []로 합치지 않음 | SRC-002:2 |', '| 응답 200 본문 | object {items:Project[], total:number}. 두 필드 모두 필수·non-null | 목록/개수의 독립 매핑은 아래 두 행 | v1 Project[] 본문으로 해석하지 않음. 실패를 성공 본문으로 합치지 않음 | SRC-002:2 v2 |\n| 응답 200 본문.items | Project[], 필수·non-null | 프로젝트 목록. 개수 산출에 items.length를 사용하지 않음 | []는 성공한 결과 없음. items가 비어도 표시 개수의 출처는 total | SRC-002:2 v2 |\n| 응답 200 본문.total | number, 필수·non-null. 정수/최댓값 등 추가 제약은 명시되지 않음 | 현재 필터 결과 개수를 그대로 표시 | {items:[],total:0}이면 0. total과 items.length가 다를 때도 total을 사용 | SRC-002:2 v2 |')
replace('| 응답 503 본문.error |', '| 응답 Project.owner_name | string, optional, null 허용. 응답 방향이며 요청 body가 아님 | 목록의 담당자 이름 | 필드 누락/null/빈 문자열은 미지정, 그 외 문자열은 그대로. trim·대소문자 변환·임의 이름 생성 없음 | SRC-002:2 v2, SRC-006:3 DEC-027; Q-010/OD-owner |\n| 응답 503 본문.error |')
replace('필수/non-null 판정은 Project의 세 필드에 명시된 범위만 확정한다.', 'items/total의 필수·non-null 및 owner_name의 optional/null은 현재 v2 원문으로 확인했다. Project의 기존 세 필드와 503 shape는 §2.1에서 명시한 기존 SPEC 계약 기술과 v2의 동일성 확인을 근거로 유지하며 원 v1 파일을 읽었다고 주장하지 않는다.')
# Replace affected canonical AC rows, retaining identities and full failure/selection scenarios.
start=s.index('| AC-1 | SRC-001:2;',s.index('### 6.1'))
end=s.index('\n### 6.2',start)
s=s[:start]+'''| AC-1 | SRC-001:2; SRC-002:2 v2; SRC-006:2; 디자인 SRC-003/005 | 프로젝트 목록 진입 및 GET 응답을 제어할 수 있음 | 첫 진입 All 조회 확인 후 All, Active, Archived, Paused를 각각 명시 선택하고 각 요청을 완료 | 첫 진입 status=all. 네 선택 항목이 보이며 query는 각각 all/active/archived/paused. 최신 200의 items에 있는 실제 이름·상태를 목록으로, total을 개수로 표시. items.length·고정 이미지 데이터·고정 개수로 대체하지 않음 | §3.1~3.2 첫 진입·Status 조회, §4 Status·목록, §5.1~5.2 GET/items/total | 구현 후 첫 요청과 네 query 대조. 0/1/여러 items 및 items 2개·total 7처럼 길이와 total이 다른 제어 응답에서 표시 개수 7 확인. label/focus, 파란 accent, 700/701px 배치 확인. 배포 Q-001; Q-002는 DEC-027로 해결 |
| AC-2 | SRC-001:3; SRC-004:1; SRC-002:2 v2; SRC-006:2 | 첫 진입에는 프로젝트 미선택; 이후 P를 포함한 성공 items가 있고 사용자가 P를 선택 | 첫 진입 및 성공 응답에서 자동선택 없음을 확인. P 선택 후 P가 없는 필터, 200+{items:[],total:0} 필터, P가 돌아오는 필터를 순서대로 조회 | 첫 진입 All 조회가 프로젝트를 자동선택하지 않음. 선택 직후 패널에 P.name. P가 목록에 없어도 패널 이름·선택 객체 유지. 빈 성공은 결과 없음과 total 0이며 오류가 아님. P가 같은 id로 재등장하면 해당 행 선택 표시 복구 | §3.2 첫 진입·행 선택·필터 밖 선택·성공 empty, §4 선택 패널, §5.1 선택/§5.2 id/name/items/total | 구현 후 items 순서·개수를 바꾸어 id 매칭 확인, 빈 성공/로딩 중 패널 유지 확인. 이미지의 주황 대신 시스템 accent 확인. 초기 미선택 문구 Q-011; 초기 동작 Q-002는 해결 |
| AC-3 | SRC-001:4; SRC-002:2 v2; SRC-004:1 | P 선택 상태에서 필터 요청과 완료 순서를 제어할 수 있음 | 현재 요청을 503으로 실패시켜 Retry; A 시작 뒤 새 필터 B 시작. 이전 A의 성공·실패·finally를 B 대기/완료 중 각각 늦게 전달 | 실패는 성공 empty와 다른 오류/Retry. Retry query는 실행 시점의 현재 필터. loading·error·Retry에도 P 유지. 최신 B만 성공 items/total 또는 실패를 화면에 반영하고 A는 목록·개수·오류·loading 종료를 바꾸지 않음. 동일 필터 Retry의 이전 요청에도 동일 규칙 | §3.2 실패·Retry·응답 역전, §4 상태/선택, §5.1/5.3 | 구현 후 200+{items:[],total:0}과 503 비교, Retry query/선택 확인. A성공→B실패, A실패→B성공의 역순 완료와 B 대기 중 A finally를 제어해 최신 상태 확인. 실제 앱 실행은 미수행; 배포 Q-001 |
| AC-owner | 기존 사용자 추가 메모·OD-owner; SRC-002:2 v2; SRC-006:3 DEC-027 | 최신 성공 200의 items를 목록에 표시; 응답의 optional owner_name 값들을 제어할 수 있음 | owner_name 누락, null, 빈 문자열, 일반 문자열, 공백만 있는 문자열을 가진 프로젝트들을 표시 | 앞의 세 경우 담당자는 미지정. 그 외 문자열은 원문 그대로 표시하며 trim하지 않음. 프로젝트 이름·상태와 목록을 유지하고 owner_name을 요청 body로 전송하지 않음 | §3.2 담당자 표시, §4 담당자, §5.2 응답 Project.owner_name | 구현 후 각 값의 표시를 대조하고 요청 body가 추가되지 않음을 확인. Q-010/OD-owner는 DEC-027로 해결; 실제 앱 실행·배포 확인은 미수행 |
''' + s[end:]
review='''### 6.2 명세 검토 결과

| 검토 | 수행 범위·방식 | 결과와 한계 |
| --- | --- | --- |
| 구조·ID·상호 참조 | 이번 작성자가 기존 SPEC revision 3/QUESTIONS revision 1과 현재 revision 4/2를 대조. 여섯 절·동반 경로·feature identity, 정본 AC-1/AC-2/AC-3/AC-owner 각 1행, Q-001/Q-002/Q-010/Q-011과 OD-owner를 검토. 변경 후 번들 helper를 새로 실행하고 output/spec-check-current.json을 읽음 | 현재 정본 표와 사용자 수동 AC-owner를 포함한 검사. 기존 spec-check.json 및 옛 ready 기록을 판정 근거로 재사용하지 않음. helper는 지원 구조·질문 상태·기록 존재만 검사하며 의미 정확성·실행 결과를 인증하지 않음 |
| 원자료·권위·판본 대조 | 이번 자기 검토에서 request/api v2/DESIGN/ux/update-decision 전체를 직접 읽고 §2.1 바이트 식별자·행·§2.3 역대조. selected-reference.png를 로컬 view_image로 직접 확인, PNG 헤더 치수 확인. DEC-027의 제품 책임자 확정 권위 및 v2 대체 범위를 확인 | items/total·개수 출처·owner_name 응답 방향과 누락/null/빈 문자열·그 외 원문, All 첫 조회·자동선택 금지를 본문에 반영. 변경 없는 Project 세 필드·503은 기존 SPEC 기록과 v2의 동일성 확인을 근거로 유지했으며 원 v1 파일은 제공되지 않음. Q-001 미확인, 정확한 미선택 문구는 Q-011 |
| 화면·정책·API·AC 정합성 | 현재 §3 초기 조회/필터/선택/empty/실패/Retry/역전/담당자를 §4 규칙·§5 GET/query/200 items/total/503 및 네 AC와 대조 | 모든 현재 매핑에서 목록은 items, 개수는 total. empty fixture는 {items:[],total:0}. 필터 밖/로딩/오류/Retry 선택 유지, 같은 id 복귀, 이전 성공·실패·finally 무효화를 보존. owner_name은 응답 전용이며 미지정 정책 일치. 상충 해석을 발견하지 못했지만 앱·실서버는 실행하지 않음 |
| AC별 구현 내용 재구성 | 별도 독자·모델 호출 없는 작성자 자기 검토. 네 AC 각각 actor/초기 상태→행동→요청 또는 순수 FE 처리→성공/실패 UI→회복을 현재 문서와 직접 읽은 원자료에서 재구성. AC-1: All/네 query·items·total, AC-2: 무자동선택·P 선택/숨김/empty/id복귀, AC-3: 503/현재 Retry/A·B 역전/finally, AC-owner: 다섯 응답값 표시 | 네 AC 모두 명시된 동작과 관찰 가능한 검증 시나리오를 재구성. Q-011은 정확한 미선택 문구에만 해당하고 초기 데이터/요청/선택 정책은 결정 완료. 독립 검토·코드 검사·앱 테스트·배포 확인은 수행하지 않음. 자기 검토의 미발견은 정확성의 독립 증명이 아님 |

- 검토 대상: 현재 SPEC revision 4, QUESTIONS revision 2, §2.1의 여섯 원자료. 이번 작성자가 실제 내용을 다시 읽고 변경 부분뿐 아니라 네 AC의 기존 실패·재시도·선택 유지 조건까지 검토했다. 현재 helper 출력과 검토·변경 기록은 `../output/`에 별도로 남긴다.
- 준비 판정 이유: 네 검토를 현재 내용에 새로 수행했고 활성 차단 질문은 없다. 기존 선언 범위를 축소하지 않았다. Q-010은 deferred+yes 상태에서 실제 DEC-027 답변으로 해결했다. Q-001은 계약 확정과 별개인 배포 검증이고 Q-011은 미선택 문구의 비차단 확인이다. 상태는 ready이며 구현·게시 권한을 부여하지 않는다.
- 수정 이력: revision 1 초안·revision 2 첫 검토의 기존 기록은 §6.3에 보존한다. 이번에 읽은 revision 3에는 사용자 USER-EDITED/AC-owner/Q-010 수동 편집과 blocked 상태가 있었고, 당시 본문의 ready 설명·검토 대상은 이 수동 편집을 포괄하지 않았다. revision 4는 v2/DEC-027에 따라 items/total·담당자·초기 진입 규칙과 네 AC·질문을 갱신하고 새 검토 결과를 반영한다. QUESTIONS는 revision 1→2이다.
- 외부 의존·미확인 범위: 실제 API 배포/구현 상태(Q-001), 현재 앱 토큰 정의·오류 컴포넌트·초기화 코드·실제 레이아웃/키보드 동작. 확정 Target contract v2와 제품 결정은 실제 배포·기존 코드 일치의 증거가 아니다. 초기 미선택 문구는 Q-011. 읽지 못한 별도 원 v1/API schema·실제 코드가 존재하는지는 unknown이며 제공되지 않았다.
- 후속 검증: §6.1 네 AC를 구현 후 실제 앱/제어 응답에서 실행해야 한다. 이 문서 작업은 그 동작을 실행하거나 실서버와 일치를 확인하지 않았다.

### 6.3 기존 검토 기록 보존 — 현재 판정에 사용하지 않음

아래는 수정 전 SPEC revision 3에 남아 있던 revision 1~2 검토 서술의 원문이다. v1/옛 질문 상태를 포함하는 역사이며 현재 규칙이나 이번 검토 결과가 아니다. 이번 검토는 §6.2, 현재 동작은 §1~§6.1, 현재 질문 상태는 QUESTIONS §1을 따른다.

```text
'''+old_review+'''```
'''
s=s[:s.index('### 6.2 명세 검토 결과')]+review+s[s.index('\n사용자 추가 메모:'):]
# Preserve manual memo exactly and explicitly mark it as historical.
replace('\n사용자 추가 메모:', '\n이전 사용자 추가 메모 원문(현재 규칙 아님; Q-010은 DEC-027로 해결했고 §2.2/§4/§5.2/AC-owner에 반영):\n\n사용자 추가 메모:')
spec_path.write_text(s)

q=q_path.read_text().replace('revision: 1','revision: 2',1)
q=q.replace('- 확인 범위: request.md, api.md(Target contract v1), DESIGN.md, ux.md 전체와 selected-reference.png를 직접 검토했다.', '- 확인 범위: 이번 갱신에서 기존 SPEC revision 3/QUESTIONS revision 1 및 request.md, api.md(Target contract v2), DESIGN.md, ux.md, update-decision.md(DEC-027) 전체를 다시 읽었고 selected-reference.png도 로컬 이미지 도구로 직접 확인했다.',1)
q=q.replace('API 계약 변경은 SPEC §5와 AC-1~AC-3,', 'API 계약 변경은 SPEC §5와 AC-1/AC-2/AC-3/AC-owner,',1)
q=q.replace('초기 진입 자료는 Q-002에 반영한다.', '초기 진입 동작 변경은 Q-002의 이력을 보존해 재개하고, 정확한 미선택 문구는 Q-011에서 확인한다. 담당자 정책은 Q-010/OD-owner 이력을 보존한다.',1)
q=q.replace('활성 차단 질문은 없으며 비차단 항목을 구현·배포 검증 완료로 해석하지 않는다.', 'Q-002/Q-010은 DEC-027의 실제 답변으로 해결했다. 활성 차단 질문은 없고 Q-001/Q-011은 비차단 미결이다. 비차단 항목을 구현·배포 검증 완료로 해석하지 않는다.',1)
start=q.index('| Q-001 | 검증 미완료 |')
end=q.index('\n## 2.',start)
q=q[:start]+'''| Q-001 | 검증 미완료 | Target contract v2가 연결할 실제 환경에 배포되어 있는가? | §5, §6.2; AC-1, AC-2, AC-3, AC-owner의 실서버 통합 검증 | no | open |
| Q-002 | 근거 부족 | 기존 화면 진입 시 초기 Status·초기 요청·미선택 패널은 어떤 관례를 사용하는가? | §2.2, §3.2, §4, §5.1; AC-1, AC-2의 최초 진입 통합 | no | resolved |
| Q-010 | 결정 필요 | 담당자 이름 누락/null 표시는 무엇인가 | AC-owner | yes | resolved |
| Q-011 | 근거 부족 | 최초 미선택 패널에 사용하는 정확한 안내 문구는 무엇인가? | §2.2, §3.1, §4; AC-2 최초 미선택 표시 문구 | no | open |
''' + q[end:]
start=q.index('### Q-001 —')
end=q.index('\n## 3.',start)
q=q[:start]+'''### Q-001 — 계약의 실제 배포 상태

- 원문 식별자: 기존 api.md v1:2의 배포 미확인 문장에 처음 연결했으며 현재 api.md v2:2도 “실제 배포 상태는 미확인이다”라고 명시한다.
- 질문: 구현/통합할 환경에서 Target contract v2 endpoint와 응답 계약을 실제로 사용할 수 있는가?
- 근거·충돌: SRC-002는 이번 변경의 확정 계약이고 items/total 및 owner_name을 정한다. 계약 미정 충돌은 없고 배포 증거만 없다. 기존 v1은 이번 원자료로 제공되지 않았으며 과거 질문 근거로 보존한다.
- 현재 확인한 사실: GET /api/projects와 네 query status, 200 {items:Project[],total:number}, optional/null owner_name 표시 계약이다. 503 {error:string}·Retry·최신성은 기존 계약 유지. 실서버를 호출하지 않았다.
- 구현 영향: 실서버 연결·통합 검증 시 실행 환경·배포 버전을 확인해야 한다. v2 제어 응답 기반 FE 구현과 네 AC 검증은 독립 진행 가능하다.
- 차단성 이유: 동작이나 schema 결정을 추측할 필요는 없다. 문서 준비는 배포 인증이 아니므로 비차단이며 실서버 검증 성공을 미리 주장할 수 없다.
- 해결에 필요한 것: 해당 환경에 v2가 배포된 버전·endpoint 확인 또는 실제 요청/응답 검증 증거.
- 결정권자·답변자: unknown.
- 필요한 시점·재확인 조건: 실서버 통합 검증 이전 또는 계약 판본/환경 변경 시.
- 해결 결과: 배포 증거 없음. v2 변경만으로 해결하지 않았다.
- SPEC 반영 위치: §2.1 SRC-002, §5, §6.1 확인 방법, §6.2 외부 의존.

### Q-002 — 초기 진입 관례의 확인

- 원문 식별자: request.md:2–5 및 selected-reference.png의 All·Tide 정적 화면. 기존 Q-ID 유지; 별도 OD-ID 없음.
- 질문: 기존 화면 진입 경로가 정하는 초기 필터·첫 조회 시점·프로젝트 미선택 상태의 표현은 무엇인가?
- 근거·이전 확인: 최초 작성 때 초기화 코드/규칙이 제공되지 않았고 정적 이미지가 자동선택·초기값을 증명하지 않아 질문으로 남겼다. 이 과거 미확인은 해결 이력으로 보존한다.
- 현재 확인한 사실·해결 결과: SRC-006 update-decision.md:1–2의 DEC-027(2026-11-10 제품 책임자 확정 답변)은 “첫 진입은 기존 All 조회를 유지하고 자동 프로젝트 선택은 하지 않는다.”이다. 따라서 첫 요청은 status=all이고 최초 패널은 프로젝트 미선택 상태이다. 기존 초기화 코드를 확인했다는 뜻은 아니다.
- 구현 영향: 첫 All 조회 유지, 응답에 프로젝트가 있어도 자동선택 금지. 사용자가 행을 선택하면 기존 이름 표시·선택 유지 계약으로 이동한다.
- 차단성 이유: 실제 확정 답변으로 초기 데이터·요청·선택 동작을 정했다. 정확한 미선택 패널 안내 문구는 답변에 없고 별개의 표현 질문 Q-011로 분리했으며, 자동선택 여부가 미정인 것처럼 남기지 않는다.
- 해결에 필요한 것: 이 초기 동작에는 추가 답변이 필요하지 않다. 실제 코드 연결/실행 검증은 후속 구현 범위이다.
- 결정권자·답변자: 제품 책임자, DEC-027.
- 필요한 시점·재확인 조건: 초기 진입 동작 요구 변경 시 기존 이력을 유지하고 재개한다.
- SPEC 반영 위치: §2.2 DEC-027/Q-002, §3.2 첫 진입, §4 Status·미선택, §5.1 첫 진입, AC-1/AC-2.

### Q-010 — 사용자 추가 질문: 담당자 누락/null 표시

- 원문 식별자: OD-owner, AC-owner. 사용자 수동 추가 질문 ID 및 관계를 유지한다.
- 질문: 응답 owner_name이 누락/null인 프로젝트의 담당자를 어떻게 표시하는가?
- 근거·이전 확인: 사용자 추가 당시 누락/null 표시 정책이 없어 deferred, 미해결 시 차단 yes로 보류했다. 이전 상세 원문은 §3.1에 그대로 보존한다.
- 현재 확인한 사실·해결 결과: SRC-006 update-decision.md:1,3의 DEC-027(2026-11-10 제품 책임자 확정 답변)과 SRC-002 api.md v2:2가 함께 확정한다. 응답 owner_name 누락/null/빈 문자열은 미지정, 그 외 문자열은 원문 그대로 표시한다. owner_name은 optional/null 허용 응답 필드이며 요청 body가 아니다.
- 구현 영향: 성공 items 목록에 담당자를 표시한다. 임의 trim/이름 생성·프로젝트 제외·새 쓰기 요청 없이 세 fallback 조건과 나머지 문자열을 구분한다. AC-owner 검증에 누락/null/빈 문자열/일반 문자열/공백 문자열을 포함한다.
- 차단성 이유: 미해결이면 AC-owner를 차단했지만 실제 확정 답변으로 해결했다. 표의 yes는 해결 전 영향이며 현재 활성 차단이 아니다. 단순 보류·무응답·제안으로 해결한 것이 아니다.
- 해결에 필요한 것: 이번 표시 정책에는 추가 답변이 필요하지 않다. 실제 앱 표시와 실서버 응답 검증은 수행하지 않았다.
- 결정권자·답변자: 제품 책임자, DEC-027.
- 필요한 시점·재확인 조건: owner_name schema 또는 표시 정책이 바뀌면 이력을 유지해 재개한다.
- SPEC 반영 위치: §1 포함 범위, §2.2/§2.3, §3.2 담당자 표시, §4 담당자, §5.2 Project.owner_name, AC-owner.

### Q-011 — 최초 미선택 패널의 정확한 문구

- 원문 식별자: Q-002의 최초 질문 중 표현 세부사항. DEC-027은 미선택 동작을 정했지만 문구 문자열은 제시하지 않았다. 동작 결정 Q-002와 다른 질문으로 분리했다.
- 질문: 자동선택이 없는 최초 패널의 안내 문구는 기존 앱에서 무엇을 사용하는가?
- 근거·충돌: SRC-005는 이미 Tide가 선택된 화면이고 SRC-006:2는 자동선택 금지만 확정한다. 정확한 미선택 문구는 원자료에 없다. 충돌하는 확정 문구는 없다.
- 현재 확인한 사실: 첫 status=all 조회, 프로젝트 자동선택 없음, 선택 전 패널에 가짜 프로젝트 이름을 채우지 않음은 SPEC에 확정했다.
- 구현 영향: 초기 미선택 패널의 안내 문자열을 연결할 때 기존 앱 관례 확인이 필요하다. 요청·데이터·초기 선택·선택 후 이름 표시 정책은 바뀌지 않는다.
- 차단성 이유: 선언 AC는 특정 안내 문자열을 요구하지 않는다. 이미 결정된 미선택 상태와 선택 후 실제 이름 표시를 구현·검증할 수 있어 동작 계약의 차단 조건이 아니다. 특정 필수 문자열 요구가 생기면 영향·차단성을 다시 판정한다.
- 해결에 필요한 것: 기존 앱 미선택 패널 문자열 확인 또는 사용자의 확정 문구.
- 결정권자·답변자: unknown.
- 필요한 시점·재확인 조건: 기존 앱 표현과 연결할 때. 코드·브라우저 확인은 이번 허용 범위에 없어 수행하지 않았다.
- 해결 결과: 확정 문자열 없음. 임의 placeholder를 확정 문구로 만들지 않았다.
- SPEC 반영 위치: §2.2, §3.1, §4, AC-2 확인 방법.
''' + q[end:]
# Original history rows remain intact; append actual new evidence and preserve the original manual note.
start=q.index('\n### Q-010 — 사용자 추가 질문',q.index('## 3.'))
original_manual=q[start+1:]
q=q[:start]+'''| Q-001 | 2026-11-10 이번 갱신; 정확한 확인 시각 미기록 | api.md v2:1–2 전체를 직접 확인, 배포 미확인 유지 | v2와 네 AC로 영향 갱신; 배포 증거 없어 open 유지 |
| Q-002 | 2026-11-10 DEC-027; 이번 갱신에서 답변 확인 | update-decision.md:1–2 제품 책임자 확정: 첫 All 조회 유지, 자동선택 없음 | SPEC §2~§5 및 AC-1/AC-2 반영, open→resolved. 정확한 안내 문자열은 다른 질문 Q-011로 분리 |
| Q-010 | 사용자 수동 추가 시; 실제 시각 unknown | OD-owner/AC-owner 담당자 표시 요청에 누락/null 정책이 없어 보류한 기존 메모 | 원 ID와 관계를 보존; deferred+yes였으며 과거 검토는 이 편집을 다루지 않았음 |
| Q-010 | 2026-11-10 DEC-027; 이번 갱신에서 답변 확인 | update-decision.md:1,3 제품 책임자 확정 및 api.md v2:2: 누락/null/빈 문자열→미지정, 나머지 그대로 | SPEC §2~§5/AC-owner 반영, deferred→resolved. 차단 yes는 역사로 유지하며 활성 차단 아님 |
| Q-011 | 2026-11-10 이번 갱신; 정확한 확인 시각 미기록 | DEC-027/정적 이미지 모두 최초 미선택 안내의 정확한 문자열은 제공하지 않음 | Q-002의 동작 결정과 표현 세부사항을 분리해 비차단 open 등록; 임의로 해결하지 않음 |

### 3.1 이전 사용자 추가 질문 원문 보존

다음은 갱신 전 질문 메모의 원문이며 과거 기록이다. 답변과 현재 상태는 §2 Q-010 및 §1 정본 표를 따른다.

```text
'''+original_manual+'''```
'''
q_path.write_text(q)
print('Patched SPEC revision 3→4 and QUESTIONS revision 1→2; preserved original user text, IDs and historical review records.')
