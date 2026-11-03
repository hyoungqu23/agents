# 프로젝트 목록 구현 결과

계산된 판정: **complete**. helper의 gaps는 `[]`이며, AC-1·AC-2·AC-3와 적용 디자인/UX 요구사항을 구현했습니다.

- 변경: `src/app.js`, `src/project-list.js`, `src/theme.css`, `tests/project-list.test.mjs`.
- 동작: All/Active/Archived/Paused 필터와 결과 수, 필터 밖에서도 선택 유지, 빈 성공·로딩·오류 구분, 현재 필터 Retry, 오래된 성공/실패 응답 무시.
- 검증: `npm test` 5개 통과, `git diff --check` 통과. 실제 Chrome 앱에서 3/2/1/0 결과, Tide 선택 유지와 복원, 로딩, Active→Archived 경합, 합성 실패와 Retry 복구를 확인했습니다.
- 디자인: 기존 UI/API 헬퍼와 파란 토큰 유지. 1280×800 좌우 배치와 375×812 세로 배치, 가로 넘침 없음, 키보드의 3px 파란 포커스를 관찰했습니다.
- 보존: 제공 문서·서버·기존 사용자 초안의 초기 바이트가 유지됐습니다. 커밋·푸시·설치·배포·외부 게시는 하지 않았습니다.

실행 앱: http://127.0.0.1:62230/ . 실행 디렉터리는 `/private/tmp/hm2-implement-forward-codex-20261030-a/source`, 명령은 `PORT=0 node server.mjs`입니다. 서버 exec session은 `85827`, 실제 Node PID는 `74427`입니다. 서버는 부모의 별도 관찰을 위해 실행 중이며 합성 mode는 `fail:false`로 복원했습니다.

환경 제약과 처리: 기본 sandbox의 루프백 listen/connect가 EPERM이어서 허용된 권한 실행으로 진행했습니다. 서브에이전트 IAB visible 탭이 지원되지 않아 Chrome을 사용했습니다. 브라우저 API가 resource timing을 노출하지 않아 직접 네트워크 추적은 남기지 못했으며, 실제 화면 결과·기존 API 코드·네이티브 테스트·실제 루프백 GET 계약 기록을 보존했습니다. 미구현 요구사항은 없습니다. 독립 코드 리뷰·Visual QA·배포는 수행하지 않았습니다.

입력 HEAD: `a30eef69718712526d8ea2fd504a3dcd982c0054`
입력 manifest SHA-256: `f960e2f714323faed70ab0899b52c79823cbec237e0fa61f4f4d96c92c886814`
baseline digest: `336c870484f132e4dbdf8c69ca820d34782eb9cdf8a2c32fa0cb7c24222899f6`
verification digest: `583411576793e009f2b816fb8844750ce033b931f09199c6dbfdc306e43d6fa7`

산출물은 이 외부 state 폴더에 있습니다:

- `inputs.json`, `target.json`, `verification-target.json`
- `result.json`, `assessment.json`, `current.diff`
- `evidence/native-tests.txt`, `evidence/browser-trace.json`, `evidence/browser-check-summary.txt`
- `evidence/loading-observation.json`, `evidence/fixture-fail-on-retry.txt`, `evidence/fixture-restored-live-contract.txt`
- `evidence/wide-layout.json`, `evidence/narrow-layout.json`, `evidence/keyboard-focus.json`
- `evidence/wide-focus.png`, `evidence/narrow.png`, `evidence/empty.png`, `evidence/error.png`
- `evidence/design-source-trace.json`, `evidence/current-source.txt`, `evidence/assessment-command.txt`

실패한 초기 환경/선택자 시도의 증거도 삭제하지 않았습니다.
