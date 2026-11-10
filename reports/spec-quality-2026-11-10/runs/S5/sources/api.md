Target v2: GET /api/projects?status=all|active|archived|paused → 200 Project[]; 각 status의 결과는 서버가 필터링한다. 503은 {error:string}.
