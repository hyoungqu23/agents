# prd-gate 실제 검증 — 2026-10-04

PR2 #13의 391f389에서 분기한 codex/product-prd-gate 작업 트리를 평가했다.
Codex CLI 0.156.1, gpt-6-astra, reasoning low를 사용했다. 모델 별칭은 불변 판본이
아니다. 각 실행의 입력/스킬/참조 스냅샷, prompt, 실제 명령 trace, 출력과 hash를
보존했다. summary.json의 commit은 부모이며 평가 대상은 미커밋 PR3 패치다.

## 개별 검토

isolated/의 4개 사례는 각각 한 번 실행했고 좁은 검사 29개가 통과했다.
전체 보고서를 입력에 대조했다.

- gate-clean: ready_for_flow, findings 없음. 기존 정확한 태그 검색·내용 열기와
  빈 결과/조회 실패 구분이 관찰 가능하다. 개인 도구에 시장 조사·새 인증·수치
  목표를 요구하지 않았다. 데이터 읽기 통합 가정은 선언한 흐름에 비차단이다.
- gate-policy: 실제 PR2 생성 PRD와 문제 정의·원자료를 소비해 needs_decision.
  문서 결함을 만들지 않고 리비전 선택·내부 권한·유보 정책의 흐름 영향을
  구분했다. 미검증 4/12 및 합성 입력 한계가 보존됐다.
- gate-stale: revise. 불관찰적인 AC-001, 익명 외부 공유 FR-003과 명시적 제외의
  충돌, 원문 대비 열기·빈/실패 결과 누락을 위치와 근거로 확인했다.
  과거 보고서와 현재 문서의 nominal revision은 모두 2지만 실제 SHA-256이
  달라 과거 ready_for_flow를 stale로 처리했다.
- gate-missing: incomplete. 승인 규칙의 유일한 근거 approval-policy.md가
  없어 필수 평가를 완료하지 못했다고 밝혔다. 승인자나 정책을 발명하지 않았다.

첫 clean/policy 결과는 제공된 기존 문서만으로 separate_invocation이라는
표현을 사용했다. 작성 이력 미제공 시 independence를 unverified로 기록하도록
지침을 명확히 했다. clean-refined/의 재실행은 같은 clean 결과를 유지하며
unverified를 명시했고 좁은 검사 7개가 통과했다. stale/missing은 보완된 지침을
실행 시점에 복사해 사용했고 unverified를 명시했다. 첫 결과를 최종 지침의
완전한 검증으로 바꾸어 표시하지 않는다.

## 한 요청의 실제 연결 — 실패와 수정

chain-initial-failed/: 작성자가 problem-frame과 prd-write를 읽어 실제 문서를
작성한 뒤 sandbox 안에서 nested codex exec를 호출했다. 로컬 OS가 app-server
초기화를 Operation not permitted로 거부해 독립 검토가 실행되지 않았다.
작성자는 보고서를 발명하지 않았고 runner는 실패를 기록했다. 이 실패 기록은
그대로 보존한다. 코드/서비스 제한을 우회하거나 자체 검토로 대체하지 않았다.

chain-bridge/: 고정된 file request capability로 연결 방식을 수정했다. 하나의
coordinating invocation이 problem.md를 작성하고 그 파일을 PRD로 소비한 뒤
작성본 SHA-256과 reviewer prompt를 저장하고 review-request.json을 제출했다.
그 요청에 따라 host ReviewerBridge가 동일 모델의 별도 ephemeral Codex CLI를
workspace-write sandbox로 실행했다. bridge는 고정 action/prompt 경로만 받으며
arbitrary command, model override, external path를 받지 않는다.

검토자가 report.md/report.json을 작성하여 ready_for_flow를 판정했다. 부모는
보고서와 작성본을 수정하지 않았다. 실제 outer/inner 명령과 전체 산출물을
대조했고 작성 전후가 아닌 **검토 전후** problem.md, prd.md, chain-notes.md의
SHA-256이 동일했다. 좁은 검사 12개가 통과했다. 별도 호출의 thread ID와
host launch/result는 실행 모델이 수정할 수 없는 workspace 바깥에도 보존한다.
부모가 문서·판정을 대신 조립한 결과가 아니다.

이 실행의 검토자는 독립성 확인을 위해 작성 명령 로그도 읽었다. 따라서
호출 분리는 확인했으나 블라인드 검토나 조직적 독립성을 주장하지 않는다.
보고서 자체도 이 한계를 밝힌다. grader의 정답/기대 판정은 전달하지 않았다.

## 코드 및 설치 검사

Python 단위/회귀 검사 32개, official Claude/Codex plugin validators, temporary
marketplace load check, skill-creator quick_validate 및 git diff --check가 통과했다.
프로세스 doubles는 임의 요청 거절, 원본 변경 검출, 잘못된/미완료 이벤트와
명시적 chain timeout 실패를 확인한다. 이 doubles는 모델 품질 증거가 아니다.

기본 local validator 경로가 없어 CI pinned openai/codex commit
5c5308fc9a9ee789049d646ef11e5400384b9c6f의 공식 validator를 임시 경로에서
CODEX_PLUGIN_VALIDATOR로 지정했다. chain 재실행 후 추가한 종료 경합 및 malformed
reviewer-event 방어는 단위 검사로 검증했다. 성공 경로는 동일하다.

## 한계와 재현

검토 4개와 연결 1개 합성 사례의 focused smoke이며 전체 15-case 모델 suite,
6개 gate rubric 전부, source-command injection과 짧은 채팅의 실제 실행,
Claude 모델, implicit discovery, 다른 모델·반복 통계와 hosted behavioral CI는
미실행이다. 일부 clean 재실행은 위 독립성 지침 확인을 위한 것뿐이다.
각 실행의 source/hash와 prompt로 정확히 어떤 판본을 사용했는지 확인해야 한다.
Markdown/JSON 작성 규약은 일반 schema validator가 아니다. 자동 graders는
일부 ID·digest·필드·판정만 검사하며 의미 전체를 보장하지 않는다.

ordinary prd-gate 사용에는 CLI/bridge가 필요 없다. 이 연결 평가에서만 별도
CLI의 설치/auth와 추가 모델 capacity가 필요하다. local CLI는 전역 skill metadata를
볼 수 있어 clean-host나 완전 격리 검증도 아니다. ready_for_flow는 기록한 내용과
선언된 흐름 단계의 판정이며 구현·배포 승인이나 제품 효과 검증이 아니다.

isolated/evaluated-harness는 당시 코드 사본이다. chain-bridge/evaluated-harness는
summary의 SHA-256과 일치하는 실행 당시 소스만 보존했다. 종료/이벤트 방어 변경
이전 reviewer.py는 해당 hash와 일치하도록 복원했으며 모델 출력은 수정하지 않았다.
