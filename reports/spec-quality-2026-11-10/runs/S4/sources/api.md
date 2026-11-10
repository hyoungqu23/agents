# Target contract v2, 이번 변경의 확정 계약
GET /api/projects?status=all|active|archived|paused → 200 {items: Project[], total:number}. items와 total은 필수·non-null이다. total은 현재 필터 결과 개수이고 화면 개수는 items.length가 아니라 total을 사용한다. Project.id/name/status는 기존과 동일하다. owner_name?:string|null은 응답 필드이고 누락/null/빈 문자열은 화면에 미지정으로 표시하며 그 외 문자열은 그대로 표시한다. 요청 body 필드가 아니다. 503 오류/Retry/최신 응답 정책은 기존과 동일하다. 실제 배포 상태는 미확인이다.
