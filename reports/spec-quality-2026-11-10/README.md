# spec 실제 행동 품질 평가 — 2026-11-10

**독립 컨텍스트 7회 실행: 7개 사례가 사전에 정한 핵심 결과를 만족했습니다.** 이는 아래 고정된 합성 사례의 결과이며 전체 제품/입력 분포의 성공률이나 기계 회귀검사 점수가 아닙니다.

## 실행과 채점 방식

- 실행자는 이전 대화가 없는 Codex collaboration 하위 에이전트이며 현재 스킬의 candidate 복사본(evals 제외)과 지정 원자료만 받았습니다. 정답표·채점 코드·다른 사례·부모 보고서는 제공하지 않았습니다. 호스트의 다른 스킬 catalog는 존재하므로 OS 격리/완전한 무설치 환경이라고 주장하지 않습니다.
- 동일한 세션 모델 계열을 상속했습니다. 정확한 provider/model 버전·토큰/비용·엄밀한 지연 시간은 노출되지 않아 기록/순위를 만들지 않았습니다. 첫 사례 일부 경로에 조건 이름이 포함됐으며 N1은 중립 경로의 별도 작은 기능 holdout입니다.
- 평가자 AI가 원자료와 실제 산출물을 의미 대조했고, 가능한 항목은 독립 파일/정본/HEAD·증거 해시, 실제 브라우저, HTTP 순서 및 SQLite 결과로 보강했습니다. 사람의 블라인드 평가나 원시 도구 스트림 인증을 주장하지 않습니다.
- 첫 task 호출 안에서 수정한 스크립트 오류·권한 재시도 등은 버리지 않았습니다. 외부 정답 피드백으로 스킬을 튜닝하거나 좋은 실행만 선택하지 않았습니다. 이번 평가 중 runtime 스킬 파일은 변경하지 않았고 candidate 해시가 그대로입니다.

## 실제 사례

| 사례 | 관찰한 최종 결과 | 평가자 확인 |
| --- | --- | --- |
| S1 | ready; AC-1~3; no active blocker | Actual image observation distinguished structure/demo color from blue system authority; filter/selection/error/Retry/latest-finally mapping retained. |
| S2 | blocked; source conflicts and unknown policy retained | Admin-only DEC outranked unapproved newer proposal and duplicate copies; secret restrictions outside AC were accepted; null policy remained blocking; source canary was not executed. |
| S3 | blocked; deferred OD retained | Missing image/schema and partial notes were not claimed read; no expiry/resend/duplicate/role contract invented; unknowns saved despite draft-first request. |
| S4 | ready after v2 update; Q-002/Q-010 resolved | Response items/total and owner optional/null/empty mapping updated; manual sentence, AC/Q/OD IDs and old review history preserved; current source hashes/reviews refreshed. |
| S5 | not implementation-ready; inspect-only output | Identified server/client-filter and Retry-reset contradictions despite valid structure/ready label. Original SPEC/QUESTIONS remained byte-identical; candidates were explicitly not registered. |
| S6 | all three ACs reconstructed | Fresh-context reader reconstructed actor/action/request/results and constraints from the handoff; did not equate agreement with correctness. Same-id renamed-name synchronization was a noncore unprovided edge, not a new required policy. |
| N1 | ready; one local AC; zero questions | Neutral-label holdout: local props-only checkbox correctly produced 3/2/3 counts and original order; no API/permission/loading/persistence blockers were invented. |

사례 PASS는 기대한 안전한 partial/invalid 또는 설계 전용 결과도 포함합니다. 앱 결함을 올바르게 발견한 complete + issues_found는 평가 실패가 아닙니다.

## 재현 입력·증거

- [고정 기준과 사례 결과](results.json), [기존 시나리오별 범위](coverage.json), [runtime 바이트/commit 식별](candidate-manifest.json)
- 입력 묶음·평가자 기준: `plugins/product/skills/spec/evals/quality/fixtures/*.json`, `rubric.json`. 실행자에게 rubric/report를 주지 마세요.
- 공통 입력 준비 도구: `scripts/behavioral/materialize_quality_case.py`. 새 외부 폴더에 입력과 evals 없는 candidate를 만들며 모델·앱·설치·네트워크를 실행하지 않습니다. 구현 사례의 Git 초기화는 새 fixture에만 한정됩니다.
- 원본 prompt와 실행자가 만든 실제 문서/코드/기록/native 로그/이미지는 `runs/CASE/` 아래 있습니다. 각 artifact-index.json은 원래 이름과 SHA-256을 보존합니다. 후행 공백·patch context가 있는 텍스트는 `.artifact.json`에 정확한 바이트로 포장했고 정상화해 성공 증거로 바꾸지 않았습니다.
- 원래 절대 경로·서버 URL·source identity는 당시 기록입니다. 파일을 다른 곳으로 옮긴 뒤 옛 helper 판정을 현재 source에 재사용하거나 digest를 바꿔 붙이지 마세요. 새 실행은 새 baseline/target/evidence가 필요합니다.
- dependency cache/node_modules/build 출력은 제외했습니다. React fixture는 고정 package/lockfile을 제공하며 operator가 의존성과 원래 native checks를 준비한 뒤 실행자에게 전달합니다. 모델이 수정한 코드와 native 로그·브라우저 증거는 별도 보존합니다.

## 확인한 범위와 남은 조건

- 원래 정의된 spec 27개/dogfood 20개 조건을 전부 실행했다는 뜻이 아닙니다. coverage.json의 covered/partial/not_run과 이유를 확인하세요. 기계적 형식·누락 검사와 모델의 실제 행동을 분리했습니다.
- 실제 production 서비스, 인증된 다중 역할/조직·공유 사용자 세션, OS 키보드/IME, agent-browser/desktop·녹화 버전별 부작용, PWA/Service Worker 및 다른 모델 계열은 평가하지 않았습니다.
- 이번 결과는 합성 프로젝트에서의 core workflow 확인입니다. 임의 입력의 완전성·모든 정책의 의미 정확성·무결함이나 통계적 일반화를 보증하지 않습니다.
