// Target v2로 전달된 생성 클라이언트. 생성 시점/스키마 SHA는 알 수 없음.
export type ShareRequest = {project_id: string; recipient_user_id: string};
export type ShareResponse = {share_id: string; expires_at: string};
