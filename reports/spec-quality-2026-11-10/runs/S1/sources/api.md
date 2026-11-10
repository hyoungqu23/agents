# Target contract v1, 이번 기능의 확정 계약
GET /api/projects?status=all|active|archived|paused. 응답 200은 Project[]이고 id:string, name:string, status:active|archived|paused가 모두 필수·non-null입니다. 빈 배열은 성공한 빈 결과입니다. 실패 503은 {error:string}이며 UI의 기존 오류/Retry 처리를 사용합니다. status가 바뀔 때 요청하고 Retry는 현재 status로 다시 요청합니다. 추가 쓰기 API나 권한 정책은 이번 범위에 없습니다. 계약의 실제 배포 상태는 이 문서로 확인하지 않았습니다.
