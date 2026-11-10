---
id: "spec:filter-review"
revision: 4
handoff_version: 1
status: ready
questions: ./QUESTIONS.md
---
# 프로젝트 필터 검토 대상
## 1. 목표·범위·제약
서버 상태 필터와 요청 실패 회복. 사용자 선택은 필터·Retry에서 유지한다.
## 2. 근거 자료·확정된 결정
api.md target v2와 decisions.md DEC-filter를 읽었다고 기존 작성자가 기록했다.
## 3. 화면·사용자 흐름·상태 전이
필터를 바꿀 때는 최초 All 목록을 클라이언트에서만 걸러 표시하고 추가 서버 요청은 하지 않는다.
## 4. UI 규칙·입력 검증·권한
Retry를 누르면 필터를 All로 바꾸고 현재 선택을 해제한 다음 All을 다시 요청한다.
## 5. API 계약·데이터 매핑·오류 처리
GET /api/projects?status=all|active|archived|paused, 응답 Project[]. 503은 오류 UI를 표시한다. 필터 전환·Retry의 요청 정책은 §3~4를 따른다.
## 6. AC·검증 시나리오
### 6.1 AC 연결
| AC ID | 근거 | 사전 조건 | 행동 | 기대 관찰 결과 | 관련 화면·흐름·API | 확인 방법·미결 참조 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-fetch | DEC-filter | 목록 로드 | 상태 필터 변경 | 선택한 status로 실제 서버 요청을 보내 해당 결과를 표시한다 | GET /api/projects | 요청 query와 결과 ID 대조 |
| AC-retry | DEC-filter | 선택·현재 필터·오류 | Retry | 현재 필터를 그대로 요청하고 선택을 유지해 회복한다 | 오류·Retry·선택 패널 | 실패 전후 필터/선택/요청 대조 |
### 6.2 명세 검토 결과
| 검토 | 수행 범위·방식 | 결과와 한계 |
| --- | --- | --- |
| 구조·ID·상호 참조 | 기존 작성자의 표 확인 | 통과라고 기재됨 |
| 원자료·권위·판본 대조 | 기존 작성자의 원문 대조 | 통과라고 기재됨 |
| 화면·정책·API·AC 정합성 | 기존 작성자의 재검토 | 통과라고 기재됨 |
| AC별 구현 내용 재구성 | 기존 작성자의 자기 검토 | 통과라고 기재됨 |
