---
id: "spec:projects"
revision: 1
handoff_version: 1
status: ready
questions: ./QUESTIONS.md
---
# 프로젝트 필터
## 1. 목표·범위·제약
읽기 전용 필터. 삭제는 제외(사용자 요청).
## 2. 근거 자료·확정된 결정
request.md의 AC-list/AC-empty와 api.md 대상 v2 계약을 읽음. 배포 미확인.
## 3. 화면·사용자 흐름·상태 전이
활성 선택 시 실제 결과와 개수. 빈 성공은 오류와 구분.
## 4. UI 규칙·입력 검증·권한
필터 외 편집 없음. 내부 컴포넌트 선택은 개발자 재량.
## 5. API 계약·데이터 매핑·오류 처리
GET /projects?status=active → 200 {items: Array}. items는 필수·non-null.
## 6. AC·검증 시나리오
### 6.1 AC 연결
| AC ID | 근거 | 사전 조건 | 행동 | 기대 관찰 결과 | 관련 화면·흐름·API | 확인 방법·미결 참조 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-list | request.md | 목록 로드 | 활성 선택 | 응답 items와 개수 표시 | GET /projects?status=active | 실제 응답 ID와 표시 ID 대조 |
| AC-empty | request.md | 성공 items=[] | 결과 렌더 | 결과 없음, 오류와 구분 | 목록 UI | 빈 성공/오류 대조 |
### 6.2 명세 검토 결과
| 검토 | 수행 범위·방식 | 결과와 한계 |
| --- | --- | --- |
| 구조·ID·상호 참조 | 두 문서 정본 대조 | ID 유지 |
| 원자료·권위·판본 대조 | request/API 직접 읽음 | v2 계획 계약, 배포 미확인 |
| 화면·정책·API·AC 정합성 | 두 AC 경로 자체 검토 | 런타임 미실행 |
| AC별 구현 내용 재구성 | 자기 검토 | 별도 리더 호출 안 함 |
