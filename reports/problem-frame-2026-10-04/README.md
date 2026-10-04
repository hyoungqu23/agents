# problem-frame 실제 평가 — 2026-10-04

`codex/product-problem-frame`의 PR1 작업 트리에서 새 스킬을 실제 Codex CLI로
실행했다. 모델은 gpt-6-astra, reasoning low, CLI 0.156.1이다. source/hash와
정확한 prompt·명령·실행 trace·원래 결과를 함께 보존했다. 모델 판본은 별칭이며
불변 모델 버전으로 확정하지 않는다. summary.json은 base commit과 dirty 상태를
기록하므로 이 결과를 출시된 commit이나 hosted CI의 증거로 사용하지 않는다.

## 결과

- problem-observed: 통과. 보고된 12명 중 4명을 보존하고 독립 검증되지 않은
  합성 입력임을 표시했다. 기존 내부 사용자·로그인 계정·익명 공유 제외와
  만료/철회 정책 미결정을 보존했다. UI·DB·개선율 목표를 만들지 않았다.
- problem-hypothesis: 통과. 질문 없이 draft를 작성했다. 대상 사용자가 아직
  정해지지 않았음을 드러내고 마찰·영향을 AS 가설로 표시했다. 고객 인터뷰,
  가짜 페르소나·측정치·선택한 제품 정책을 만들지 않았다.
- problem-update: 통과. EV-001의 현재 전달 방식을 email link로 갱신했다.
  document ID, EV/DEC/OD IDs, 내부 사용자 범위, 링크 만료 미결정과 무관한
  2026-11-12 tentative 일정이 보존됐다. revision만 2→3으로 증가했다.

자동 grader의 15개 좁은 검사가 모두 통과했고, 부모가 세 산출물과 실제 명령
trace를 원자료에 대조했다. 명령은 로컬 입력·스킬·참조 읽기와 요청된 출력
확인으로 한정됐다. 원본/스킬 변경은 hash 비교에서 검출되지 않았다.

## 구조·설치 검증

- Python 단위/기존 회귀 검사 23개 통과.
- Claude/Codex 공식 플러그인 검증 통과.
- 임시 marketplace 설치에서 product가 enabled로 로딩됨.
- git diff --check 통과.

기본 ~/.codex plugin-creator validator 경로는 현재 설치에서 사라져 첫 검증이
실패했다. 검사를 생략하지 않고 저장소 CI와 동일한 공식 openai/codex commit
5c5308fc9a9ee789049d646ef11e5400384b9c6f의 validator와 형제 imports를 임시
경로에 받아 CODEX_PLUGIN_VALIDATOR로 지정했다. 관련 구현을 수정하지 않았다.

## 범위와 한계

이것은 3개 focused smoke 사례의 평가다. 6개 rubric 사례 전부, source injection
fixture의 실제 실행, 짧은 대화 모드, 실제 Claude 모델, 자동 skill discovery,
hosted CI, 다른 모델/여러 반복 실행은 미실행이다. 공유 문서 계약은 Markdown
authoring convention이며 grader가 YAML 전체나 제품 의미를 검증하는 것은 아니다.

예상 단어 포함·ID 보존만으로 semantic 품질을 보장하지 않는다. 부모가 전체
산출물을 읽어 위 판단을 내렸으나 이 사례에서의 확인일 뿐이다. PRD 작성·검토는
아직 포함되지 않았고 별도 후속 스택에서 이 산출물을 실제로 소비해야 한다.

이 평가에서 원문·정답·rubric은 실행 모델에 함께 주지 않았다. 현재 local CLI는
전역 skill metadata를 볼 수 있어 완전한 clean-host 테스트가 아니며, 각 요청은
복사한 스킬의 명시적 경로를 읽도록 실행했다. 초기 실패/재채점으로 통과를 만든
모델 실행은 없고 세 사례는 각각 한 번의 실제 실행으로 통과했다.
