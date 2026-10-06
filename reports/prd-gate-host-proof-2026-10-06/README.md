# PR #14 P2 보완 검증 — 2026-10-06

기존 연결 평가가 작성자 공간의 결과 파일을 신뢰하여 검토자를 실행하지 않고도
통과하는 경로를 수정했다. runner는 host의 메모리 결과를 받아 실제 종료/완료를
확인한다. 검토자는 별도 workspace에서 원문과 초기 스킬 snapshot을 읽고 보고서를
작성한다. host가 입력 및 report.md/report.json SHA-256을 기록한 뒤 작성자 공간에
보고서를 복사하며, 최종 grader는 원래 보고서 hash와 비교한다. 작성자 공간의
review-result.json은 상태 알림일 뿐 권위 있는 판정 근거가 아니다.

## 확인한 동작

- process-double 회귀: 검토 요청 없이 저장된 결과·이벤트 복사 → runner 실패.
- host의 실제 검토 실패 → 작성자 공간이 성공을 주장해도 실패.
- 검토 후 Markdown 또는 JSON 보고서 교체 → digest 불일치로 실패.
- 완료 이벤트만 있고 보고서가 없는 검토 → 실패.
- 검토자 입력 및 스킬 snapshot 변경 → 실패.
- Python 단위/회귀 검사 36개 통과, diff --check 통과.
- 캐시 PyYAML 및 pinned 공식 validator로 Codex/Claude 형식 검사 통과,
  임시 marketplace load-check 통과. 수정 diff 별도 read-only 리뷰에서 추가 발견 없음.

## 실제 실행

summary.json과 product-chain/은 Codex CLI 0.156.1, gpt-6-astra, low로 수행한
한 요청의 문제 정의→PRD 작성→별도 검토 실행이다. grader 14개가 통과했다.
검토자가 ready_for_flow를 판정했으며 host의 returncode=0/completed 및 입력
hash 보존을 확인했다. reviewer/의 원래 보고서와 published/의 최종 보고서가
host report_sha256과 일치한다. 부모가 보고서를 조립·수정하지 않았다.
실행 당시 스킬/참조 snapshot, prompt, outer/inner events 및 host 결과를 보존했다.
이 성공 실행 뒤에 추가한 스킬 snapshot 보존 오류 경로는 단위 검사로 확인했다.

## OS 쓰기 경계

임시 디렉터리의 기본 추가 쓰기 권한을 제외하기 위해 product-chain 호출에
sandbox_workspace_write.exclude_slash_tmp=true와 exclude_tmpdir_env_var=true를
명시했다. 사용자 전역 설정은 바꾸지 않았다. 설정 의미는
[OpenAI 공식 구성 참조](https://learn.chatgpt.com/docs/config-file/config-reference)에 따른다.

sandbox-probe/은 최종 설정을 사용한 실제 Codex CLI/모델의 OS 검사다. Python 명령은
own.txt 쓰기에 성공했고 ../sibling.txt 쓰기는 PermissionError로 거부됐다. 원래
sibling 파일도 그대로다. 권한 상승이나 sandbox 우회를 사용하지 않았다.
직접 codex sandbox 명령으로 먼저 확인하려던 시도는 로컬 permission-profile
구성 요구로 실행되지 않아 증거로 사용하지 않는다.

연결 실행은 임시 쓰기 제외 설정 추가 직전에 수행했고, 설정의 영향은 위 좁은
실제 OS 검사와 최종 command 회귀 검사로 확인했다. 전체 연결 모델 실행을
이 설정 추가 후 다시 수행한 것으로 표시하지 않는다.

## 한계

한 합성 연결 사례와 한 OS 쓰기 검사이며 전체 모델 suite·다른 OS·다른 CLI·
Claude·암묵적 발견·반복 품질 통계는 검증하지 않았다. OS 격리는 테스트한 로컬
설정/경로에 대한 증거이며 모든 호스트 설정의 보장이 아니다. summary의 commit은
부모 c3c03cf이며 평가 대상은 미커밋 수정이다. 보존된 evaluated-harness hash와
실행 당시 summary의 hash가 일치한다. 모델 정답/rubric은 전달하지 않았다.


반영 전 원격 PR #14가 64734d7로 rebase된 것을 확인했다. c3c03cf와 그 커밋의
전체 tree가 동일하므로 보존된 실행은 동일한 원문 코드를 대상으로 한다.
수정은 최신 원격 head 위에 적용하여 기존 원격 변경을 보존했다.
