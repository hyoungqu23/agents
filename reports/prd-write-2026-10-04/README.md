# prd-write 실제 평가 — 2026-10-04

PR1 #12의 de68aff 위에 만든 별도 `codex/product-prd-write` 작업 트리에서
Codex CLI 0.156.1, gpt-6-astra, reasoning low로 세 사례를 각각 한 번 실행했다.
이 모델 ID는 별칭이며 불변 판본을 보장하지 않는다. 정확한 입력·스킬/참조
스냅샷·prompt·명령 trace·출력·hash·좁은 grader 결과를 보존했다.
summary.json의 commit은 부모 de68aff이며 평가 대상은 미커밋 PR2 패치다.
실행 후 플러그인 소개 문구를 PRD 작성까지 표시하도록 보완했다.

## 결과와 산출물 대조

- prd-from-problem: PR1의 실제 problem-frame 산출물 revision 1과 원자료를
  소비했다. 12명 중 4명의 합성·미검증 수치, EV/DEC/OD 의미와 ID를 보존했고
  GOAL/FR/AC를 근거에 연결했다. 기존 내부 사용자만 대상으로 삼고 만료,
  복사/내보내기, 철회 정책을 확정하지 않았다. 리비전 선택·문서별 권한도
  새로운 열린 질문으로 드러냈다. 상태는 needs_decision이다.
- prd-update: FR-002/AC-002의 전달 경로만 이메일에서 기존 내부 포털로
  바꾸고 변경 출처·이력을 추가했다. document/GOAL/FR/AC/DEC/OD ID,
  FR-001/AC-001, 내부 사용자 범위, 만료 미결정 및 무관한
  2026-11-12 tentative 일정은 보존됐다. revision은 2→3으로 증가했다.
- prd-direct: 개인 독서 노트 요구를 직접 PRD로 작성했다. 고객 수요가
  검증되지 않은 제안임을 보존하고, 태그 연결과 노트 존재를 AS 가정으로
  명시했다. 삭제·수치 성능은 미정이며 팀 공유·새 인증·출시일을 추가하지
  않았다. 가짜 problem.md나 upstream dependency를 만들지 않았다.

자동 grader의 총 17개 좁은 검사가 통과했다. 전체 세 산출물을 원자료에
대조해 수용 기준의 관찰 가능성, 가정·결정 구분, 정책과 범위 보존을 확인했다.
실제 명령 trace는 입력·지정 스킬·참조 읽기와 요청 출력 작성·확인이다.
원본/스킬 변경은 hash 검사에서 발견되지 않았다. 코드 구현·commit·게시,
독립 PRD gate는 실행하지 않았다.

## 구조 검증

Python 단위/회귀 검사 25개, skill-creator quick_validate, Claude/Codex 공식
플러그인 검증, 임시 marketplace 로딩, git diff --check가 통과했다.
기본 로컬 plugin-creator validator가 없어 PR1과 같은 CI pinned
openai/codex commit 5c5308fc9a9ee789049d646ef11e5400384b9c6f의 공식 validator를
임시 경로에서 CODEX_PLUGIN_VALIDATOR로 지정했다. 검사를 생략하지 않았다.

## 한계

5개 rubric 전체가 아닌 세 focused smoke 사례다. 별도 정책 충돌/권위 판정,
읽기 전용 대화 사례, 실제 Claude 실행, 암묵적 skill discovery, hosted PR2 CI,
다른 모델과 반복 실행은 검증하지 않았다. 기존 비제품 smoke는 이번 모델
실행에서 반복하지 않았고 Python 회귀 검사만 수행했다.

grader는 Markdown의 일부 scalar/ID/문구만 확인하며 YAML 전체나 제품 품질을
판정하지 않는다. 전체 산출물 대조도 이 세 합성 사례의 증거로 한정한다.
원문만 실행 모델에 주고 정답/rubric은 전달하지 않았지만 전역 skill metadata가
보이는 local CLI 환경이므로 완전한 clean-host 설치 검증은 아니다.
PRD gate, flow, 화면/기술 명세는 이번 스택에 포함하지 않는다.
