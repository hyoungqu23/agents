# 공유 API target v2, 계약 검토본
POST /api/shares 요청: project_id:string 필수, recipient_user_id:string 필수.
200 응답: share_id:string 필수, expires_at:string|null 필수.
403 응답: {code:"not_allowed"}.
expires_at이 null인 경우의 사용자 표시/만료 정책은 이 계약에 정의되지 않았다. 실제 배포 여부는 이 자료에서 확인하지 못했다.
