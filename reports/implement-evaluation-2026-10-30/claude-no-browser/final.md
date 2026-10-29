## 결과 보고

Helper가 계산한 상태는 **`partial`**입니다. 코드 구현과 명령/정적 검사는 모두 통과했습니다. 다만 이번 작업에서는 브라우저를 쓸 수 없어서, 실제 앱 화면을 확인하는 필수 browser 검사(`app-browser`)는 실행하지 않았습니다(`not_run`). 그래서 5개 요구사항 모두 화면 결과가 미검증으로 남아 있습니다. 이 외의 gap은 없습니다.

### 변경 사항 (`src/`, `tests/`만 수정)
- **`src/projectList.js` (신규)**: DOM 없이 목록 상태를 관리합니다.
  - 상태 필터, 표시 중인 목록, 선택된 프로젝트를 각각 따로 보관합니다.
  - 상태는 loading / ready / error 세 가지입니다.
  - 다시 불러올 때는 현재 필터를 그대로 씁니다.
  - 필터를 빠르게 바꾸면 마지막 요청의 응답만 화면에 반영합니다.
- **`src/app.js`**:
  - 목록 위에 `selectField`로 라벨이 붙은 Status 선택기(All/Active/Archived/Paused)와 결과 개수를 넣었습니다.
  - 상태별 화면: 로딩 중 표시, 빈 결과(`No paused projects.`), 오류는 기존 `showProblem`과 Retry 버튼, 결과는 `renderRows`로 그립니다.
  - Selected project 패널은 로딩 중이나 오류가 나도 지워지지 않습니다.
- **`src/theme.css`**: `.filter`, `.empty`, `.status` 스타일을 추가했습니다. 기존 `--space`/`--line` 토큰만 사용했습니다.
- **`tests/projectList.test.mjs`, `tests/server.test.mjs` (신규)**:
  - 선택 상태 관리 로직을 검증하는 테스트 4개
  - 제공된 서버를 `PORT=0`으로 띄워 실제 API 응답과 `/__fixture__/mode` 실패 모드를 확인하는 테스트

### 검사
- `npm test`: **6/6 통과** (exit 0). 출력은 `state/evidence/npm-test.txt`에 있습니다.
- 정적 검사 **통과** (`state/evidence/static-trace.txt`):
  - `node --check` 정상
  - 기존 UI 헬퍼 사용 확인
  - 프로토타입의 주황색 강조가 코드에 없음
  - `user-draft.md`, `server.mjs`, `index.html`이 작업 전과 같음 (해시 비교)
- `app-browser`: **실행 안 함**. 화면 렌더링, 포커스 표시, 넓은 화면/좁은 화면 레이아웃, 실제 Retry 클릭은 확인되지 않았습니다.

### 디자인 차이 (의도적으로 적용)
- 선택 강조는 프로토타입의 주황색 대신 앱 기본 파란색 `--accent`를 씁니다.
- 프로젝트 행은 기존 `renderRows`의 `Name — status` 형식을 따라 상태가 소문자로 표시됩니다.
- 로딩/빈 결과 화면은 프로토타입에 없어서 ux.md 기준으로 추가했습니다.

### 남은 작업
- 브라우저로 직접 확인해야 합니다. `cd source && PORT=0 npm start`로 띄우고, 출력된 loopback URL에서 아래를 확인하면 됩니다(같은 내용이 `result.json`의 handoff에도 있습니다).
  1. Tide 선택 → Archived로 바꿔도 패널에 Tide 유지 → All로 돌아오면 Tide 강조 복원
  2. Paused 선택 시 빈 결과 화면 표시
  3. 실패 모드(`{"fail":true}`)에서 필터를 바꾸면 오류와 Retry 표시, 실패 모드를 끄고 Retry 하면 현재 필터로 다시 불러옴
  4. 너비 700px 초과/이하에서 레이아웃 확인
- 코드 리뷰와 Visual QA는 진행하지 않았습니다. 커밋도 하지 않았습니다.
- 셸 명령 두 개가 권한 승인 대기 중 자동 거부됐고, 다른 방식의 명령으로 같은 작업을 마쳤습니다. 정적 검사는 `state/static-trace.sh` 스크립트로 대신 실행했습니다.

기록 파일은 모두 `/private/tmp/hm2-implement-forward-claude-20261030-b/state/`에 있습니다: `inputs.json`, `target.json`, `verification-target.json`, `result.json`, `assessment.json`, `evidence/`