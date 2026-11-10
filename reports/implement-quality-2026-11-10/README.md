# implement 실제 행동 품질 평가 — 2026-11-10

**독립 컨텍스트 5회 실행: 5개 사례가 사전에 정한 핵심 결과를 만족했습니다.** 이는 아래 고정된 합성 사례의 결과이며 전체 제품/입력 분포의 성공률이나 기계 회귀검사 점수가 아닙니다.

## 실행과 채점 방식

- 실행자는 이전 대화가 없는 Codex collaboration 하위 에이전트이며 현재 스킬의 candidate 복사본(evals 제외)과 지정 원자료만 받았습니다. 정답표·채점 코드·다른 사례·부모 보고서는 제공하지 않았습니다. 호스트의 다른 스킬 catalog는 존재하므로 OS 격리/완전한 무설치 환경이라고 주장하지 않습니다.
- 동일한 세션 모델 계열을 상속했습니다. 정확한 provider/model 버전·토큰/비용·엄밀한 지연 시간은 노출되지 않아 기록/순위를 만들지 않았습니다. 첫 사례 일부 경로에 조건 이름이 포함됐으며 N1은 중립 경로의 별도 작은 기능 holdout입니다.
- 평가자 AI가 원자료와 실제 산출물을 의미 대조했고, 가능한 항목은 독립 파일/정본/HEAD·증거 해시, 실제 브라우저, HTTP 순서 및 SQLite 결과로 보강했습니다. 사람의 블라인드 평가나 원시 도구 스트림 인증을 주장하지 않습니다.
- 첫 task 호출 안에서 수정한 스크립트 오류·권한 재시도 등은 버리지 않았습니다. 외부 정답 피드백으로 스킬을 튜닝하거나 좋은 실행만 선택하지 않았습니다. 이번 평가 중 runtime 스킬 파일은 변경하지 않았고 candidate 해시가 그대로입니다.

## 실제 사례

| 사례 | 관찰한 최종 결과 | 평가자 확인 |
| --- | --- | --- |
| I1 | complete; all three original ACs | Consumed actual S1 output in React/TypeScript. Existing API/hook/UI owners and blue tokens reused. Native checks and real browser completed; parent independently verified UI and source/evidence. Initial result-generation syntax error was retained and recovered within the same task. |
| I2 | partial; browser not_run | Actual Node implementation and meaningful native checks; no fake browser pass. Parent later observed the actual UI independently and the existing grader passed all15 criteria without upgrading the actor result. |
| I3 | partial; AC-4 needs_decision/Q-001 | All four canonical ACs retained; independent AC1~3 implemented, archive contract not invented. Corrected an initial manifest before editing and preserved both baselines; selected baseline2 matches original source hashes. |
| I4 | partial; fresh target; unavailable browser | Same revision label with changed source and a truncated upstream list: AC3 restored, fresh baseline used, exact empty text updated, old state and dirty user CSS/draft preserved. Auxiliary diff check warned on readonly input whitespace introduced by fixture preparation; actor correctly preserved it. |
| I5 | design only; no implementation claim | Explicit design intent respected despite implement invocation. Only bounded design output written; app and candidate unchanged; no server/browser/helper execution was claimed. |

사례 PASS는 기대한 안전한 partial/invalid 또는 설계 전용 결과도 포함합니다. 앱 결함을 올바르게 발견한 complete + issues_found는 평가 실패가 아닙니다.

## 재현 입력·증거

- [고정 기준과 사례 결과](results.json), [기존 시나리오별 범위](coverage.json), [runtime 바이트/commit 식별](candidate-manifest.json)
- 입력 묶음·평가자 기준: `plugins/build/skills/implement/evals/quality/fixtures/*.json`, `rubric.json`. 실행자에게 rubric/report를 주지 마세요.
- 공통 입력 준비 도구: `scripts/behavioral/materialize_quality_case.py`. 새 외부 폴더에 입력과 evals 없는 candidate를 만들며 모델·앱·설치·네트워크를 실행하지 않습니다. 구현 사례의 Git 초기화는 새 fixture에만 한정됩니다.
- 원본 prompt와 실행자가 만든 실제 문서/코드/기록/native 로그/이미지는 `runs/CASE/` 아래 있습니다. 각 artifact-index.json은 원래 이름과 SHA-256을 보존합니다. 후행 공백·patch context가 있는 텍스트는 `.artifact.json`에 정확한 바이트로 포장했고 정상화해 성공 증거로 바꾸지 않았습니다.
- 원래 절대 경로·서버 URL·source identity는 당시 기록입니다. 파일을 다른 곳으로 옮긴 뒤 옛 helper 판정을 현재 source에 재사용하거나 digest를 바꿔 붙이지 마세요. 새 실행은 새 baseline/target/evidence가 필요합니다.
- dependency cache/node_modules/build 출력은 제외했습니다. React fixture는 고정 package/lockfile을 제공하며 operator가 의존성과 원래 native checks를 준비한 뒤 실행자에게 전달합니다. 모델이 수정한 코드와 native 로그·브라우저 증거는 별도 보존합니다.

## 확인한 범위와 남은 조건

- 원래 정의된 spec 27개/dogfood 20개 조건을 전부 실행했다는 뜻이 아닙니다. coverage.json의 covered/partial/not_run과 이유를 확인하세요. 기계적 형식·누락 검사와 모델의 실제 행동을 분리했습니다.
- 실제 production 서비스, 인증된 다중 역할/조직·공유 사용자 세션, OS 키보드/IME, agent-browser/desktop·녹화 버전별 부작용, PWA/Service Worker 및 다른 모델 계열은 평가하지 않았습니다.
- 이번 결과는 합성 프로젝트에서의 core workflow 확인입니다. 임의 입력의 완전성·모든 정책의 의미 정확성·무결함이나 통계적 일반화를 보증하지 않습니다.

I1은 새 spec 실행의 실제 SPEC/QUESTIONS를 React/TypeScript 앱으로 소비했습니다. 평가자도 별도 브라우저에서 3/2/1/0 결과·선택·오류/Retry·700/701px·focus를 확인했습니다. 첫 생성 코드 전체는 보존했고 I4 후속 변경 뒤의 앱으로 I1을 다시 채점하지 않았습니다.

I1의 초기 result 생성 문법 오류/파일 부재 invalid와 I3의 편집 전 manifest 보정 기록을 보존했습니다. 최종 상태는 같은 task 안에서 복구한 결과입니다. I4에는 fixture 준비 중 readonly SPEC의 비정본 표에 후행 공백도 남았고, 실행자는 추가 diff 검사의 경고를 숨기거나 원문을 수정하지 않았습니다. 이는 준비 입력의 부수 결함으로 기록하며 구현 결과 실패로 세지 않았습니다.

React/TypeScript와 기존 API/hook/UI owner 재사용은 실행했지만 Next.js/TanStack Query 통합은 평가하지 않았습니다.
