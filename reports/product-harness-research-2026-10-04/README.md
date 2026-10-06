# 공개 Product Harness 조사 — 2026-10-04

## 조사 목적과 범위

HM2의 `problem-frame`, `prd-write`, `prd-gate` 첫 버전을 설계하기 위한 조사다.
스타 수가 큰 공개 저장소 중 명세·PRD·의도 확인·문서 검토와 직접 관련된
7개를 목적 표본으로 골랐다. GitHub 전체의 순위표나 최신 상승률 조사는 아니다.
스타 수는 관심도를 나타내는 현재 스냅샷이며 품질·실제 수요·비용 절감의 증거가 아니다.

REST API로 star·fork·archived·기준 commit을 확인했다. 공식 저장소와 선택한
PRD/명세/질문/검토 파일의 관련 부분을 읽었다. 패키지를 설치하거나 실제
워크플로를 실행하지 않았고, 모든 리소스를 전수 감사하지 않았다. 다운로드한
파일 목록은 source-index.json에 있다. 원문 실행 지시는 참고 자료로만 다뤘다.

## 조사 대상

| 저장소 | Stars | 상태 | 기준 ref | 라이선스 확인 |
| --- | ---: | --- | --- | --- |
| [github/spec-kit](https://github.com/github/spec-kit) | 140,073 | active / not archived | `ae5ade7234be` | API 표기 MIT |
| [obra/superpowers](https://github.com/obra/superpowers) | 295,112 | active / not archived | `8ca22dba9a94` | API 표기 MIT |
| [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 71,024 | active / not archived | `2500d6da9713` | API 표기 MIT |
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53,767 | active / not archived | `3cae711ea527` | API NOASSERTION; 실제 LICENSE는 MIT + 상표 고지 (이력/법적 적합성 판단 아님) |
| [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | 64,385 | archived: 역사적 참고 | `bdcaab2c752d` | API 표기 MIT |
| [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 25,387 | active / not archived | `9af474a70e7f` | API 표기 MIT |
| [garrytan/gstack](https://github.com/garrytan/gstack) | 135,008 | active / not archived | `4015c2870b06` | API 표기 MIT |

관찰일: 2026-10-04 (Asia/Seoul). 개별 API 호출이 같은 순간에 이루어진 것은 아니다.
인기도 숫자와 구현 판본을 함께 고정했고, 조사 완료 이후의 변경은 반영하지 않았다.
GSD의 archived 여부는 API에서 확인했으며 다른 fork를 정통 후속 프로젝트로 임의
지정하지 않았다. BMAD 라이선스는 API 분류만으로 단정하지 않고 본문을 확인했다.

## 참고할 구조와 이번에 제외할 구조

### github/spec-kit

- 원문에서 확인: 독립적으로 확인할 수 있는 사용자 시나리오, 안정적인 요구 ID, clarification과 read-only analyze.
- HM2에 반영할 제안: problem→goal→requirement→AC 연결, 영향이 큰 미결정만 질문, 수정과 검토 분리.
- 제외할 제안: constitution·기술 계획·tasks·implement까지의 런타임, 고정 질문 수·선택지 형식, 근거 없는 성과 목표 기본값.
- 근거: [templates/spec-template.md](https://github.com/github/spec-kit/blob/ae5ade7234be5cb1d975f736c4e06dd46d1326d6/templates/spec-template.md), [templates/commands/specify.md](https://github.com/github/spec-kit/blob/ae5ade7234be5cb1d975f736c4e06dd46d1326d6/templates/commands/specify.md), [templates/commands/clarify.md](https://github.com/github/spec-kit/blob/ae5ade7234be5cb1d975f736c4e06dd46d1326d6/templates/commands/clarify.md), [templates/commands/analyze.md](https://github.com/github/spec-kit/blob/ae5ade7234be5cb1d975f736c4e06dd46d1326d6/templates/commands/analyze.md).

### obra/superpowers

- 원문에서 확인: 기존 맥락에서 의도 확인, 답변과 가정 분리, 작업 규모에 따른 경로와 문서 검토.
- HM2에 반영할 제안: 이미 답한 질문 생략, 초안의 불확실성 표시, 작성자와 판정 역할 분리.
- 제외할 제안: 모든 창작 작업의 필수 activation, 단계별 승인·커밋, 가장 무거운 절차를 택하는 규칙.
- 근거: [skills/brainstorming/SKILL.md](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/brainstorming/SKILL.md), [skills/brainstorming/spec-document-reviewer-prompt.md](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/brainstorming/spec-document-reviewer-prompt.md).

### Fission-AI/OpenSpec

- 원문에서 확인: proposal에서 specs/design을 분리하고 산출물 requires 관계를 선언; 구체적 WHEN/THEN 시나리오.
- HM2에 반영할 제안: 세 단계의 실제 산출물 의존성, 최소 문서, 요구사항 변경 이력.
- 제외할 제안: OpenSpec CLI 필수 의존, 기술 design·tasks·apply·archive 전면 이식.
- 근거: [schemas/spec-driven/schema.yaml](https://github.com/Fission-AI/OpenSpec/blob/2500d6da971336167548b53731a35b2127df35ac/schemas/spec-driven/schema.yaml), [schemas/spec-driven/templates/proposal.md](https://github.com/Fission-AI/OpenSpec/blob/2500d6da971336167548b53731a35b2127df35ac/schemas/spec-driven/templates/proposal.md), [schemas/spec-driven/templates/spec.md](https://github.com/Fission-AI/OpenSpec/blob/2500d6da971336167548b53731a35b2127df35ac/schemas/spec-driven/templates/spec.md), [skills/openspec-explore/SKILL.md](https://github.com/Fission-AI/OpenSpec/blob/2500d6da971336167548b53731a35b2127df35ac/skills/openspec-explore/SKILL.md).

### bmad-code-org/BMAD-METHOD

- 원문에서 확인: 제품 brief 및 PRD의 Create/Update/Validate, 상황에 맞춘 문서 분량·섹션, 기존 입력 재대사.
- HM2에 반영할 제안: 초안/갱신/검토 분리, 작은 개인 기능에 맞는 문서, 출처와 미결정 추적.
- 제외할 제안: _bmad 설치·config·memlog 스크립트, 광범위 역할·외부 시스템 handoff, 수익·페르소나 문서 강제.
- 근거: [LICENSE](https://github.com/bmad-code-org/BMAD-METHOD/blob/3cae711ea5274cf7c7cf6e173bb8d7f29cd71497/LICENSE), [skills/bmad-product-brief/SKILL.md](https://github.com/bmad-code-org/BMAD-METHOD/blob/3cae711ea5274cf7c7cf6e173bb8d7f29cd71497/skills/bmad-product-brief/SKILL.md), [skills/bmad-prd/SKILL.md](https://github.com/bmad-code-org/BMAD-METHOD/blob/3cae711ea5274cf7c7cf6e173bb8d7f29cd71497/skills/bmad-prd/SKILL.md), [skills/bmad-prd/references/validate.md](https://github.com/bmad-code-org/BMAD-METHOD/blob/3cae711ea5274cf7c7cf6e173bb8d7f29cd71497/skills/bmad-prd/references/validate.md), [skills/bmad-prd/assets/prd-validation-checklist.md](https://github.com/bmad-code-org/BMAD-METHOD/blob/3cae711ea5274cf7c7cf6e173bb8d7f29cd71497/skills/bmad-prd/assets/prd-validation-checklist.md).

### gsd-build/get-shit-done

- 원문에서 확인: 요구 ID, v1/v2/out-of-scope 구분, phase 추적.
- HM2에 반영할 제안: 현재 범위와 이후 범위 분리, 요구 누락 표시.
- 제외할 제안: 실행 로드맵·자동화 전체, archived 저장소를 최신 활성 기준선으로 취급.
- 근거: [README.md](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/README.md), [commands/gsd/new-project.md](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/commands/gsd/new-project.md), [get-shit-done/templates/requirements.md](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/get-shit-done/templates/requirements.md).

### EveryInc/compound-engineering-plugin

- 원문에서 확인: brainstorm의 WHAT과 plan의 HOW 구분, 기존 requirement 재사용, 입력에 맞춘 문서 깊이.
- HM2에 반영할 제안: problem-frame은 문제, prd-write는 사용자 결과, 기술 계획은 후속 역할로 분리.
- 제외할 제안: compound 반복 실행·외부 공유·모델 elevation·문서 마무리 메뉴 전체.
- 근거: [skills/ce-brainstorm/SKILL.md](https://github.com/EveryInc/compound-engineering-plugin/blob/9af474a70e7f2a844338519ad9e92aafbd92d4fb/skills/ce-brainstorm/SKILL.md), [skills/ce-plan/SKILL.md](https://github.com/EveryInc/compound-engineering-plugin/blob/9af474a70e7f2a844338519ad9e92aafbd92d4fb/skills/ce-plan/SKILL.md).

### garrytan/gstack

- 원문에서 확인: office-hours의 실제 현재 대안·행동 근거 확인, startup/builder의 질문 맥락 구분.
- HM2에 반영할 제안: 문제의 현재 대안과 근거, 이미 답한 질문 생략, 개인/내부 프로젝트의 목적별 질문.
- 제외할 제안: 돈·수요를 모든 기능의 필수 게이트로 취급, 거친 심문 말투, gstack 설치 의존.
- 근거: [office-hours/sections/phase-2a-startup-diagnostic.md](https://github.com/garrytan/gstack/blob/4015c2870b064644131ed6f7cfcc1469cfe9808c/office-hours/sections/phase-2a-startup-diagnostic.md), [office-hours/sections/phase-2b-builder-brainstorm.md](https://github.com/garrytan/gstack/blob/4015c2870b064644131ed6f7cfcc1469cfe9808c/office-hours/sections/phase-2b-builder-brainstorm.md), [office-hours/sections/design-and-handoff.md](https://github.com/garrytan/gstack/blob/4015c2870b064644131ed6f7cfcc1469cfe9808c/office-hours/sections/design-and-handoff.md).

## 종합 판단

세 스킬의 신규 가치는 범용 코딩 하네스를 또 제공하는 데 있지 않다. 사용자의
관측·가정·결정을 구분해 제품 요구사항으로 남기고, 이후 단계가 무엇을 근거로
했는지 확인할 수 있게 하는 데 있다.

1. `problem-frame`: 해결할 문제와 근거, 현재 대안, 미확인 가정을 남긴다.
2. `prd-write`: 그 문제에서 목표·scope·검증 가능한 AC를 도출한다.
3. `prd-gate`: 문제·사용자·scope·AC·근거 연결을 읽기 전용으로 판정한다.

가설 단계의 문서 작성 자체를 막지 않되, 그것을 검증된 고객 수요로 표시하지
않는다. 검토자가 finding을 최소 하나 만들어내게 하지 않는다. 기술 스택·화면
명세·실행 작업은 이 첫 버전의 밖이며 기존 design/review를 새로 복제하지 않는다.

질문 한 개씩 진행하는 upstream의 방식은 깊은 대화에는 유용하지만 반복 단위
작업에는 마찰이 된다. HM2에서는 이미 받은 답을 재사용하고, 영향이 큰 질문을
짧게 묶어 확인하는 기본값을 제안한다. 제품 상황과 사용자 지시에 따라 깊이를 조절한다.

## 도입과 재구현의 판단

기존 도구가 이미 원하는 입출력·질문 방식·검토 경계를 만족하면 그대로 활용하는
선택도 유효하다. 이번 HM2안은 기존 마켓플레이스의 독립 설치, 작은 질문 예산,
프로젝트 자료의 정본 존중, 세 개의 분리된 진입점이라는 차이를 구현한다.
외부 스킬의 이름만 바꿔 복제하거나 설치되지 않은 개인 자산에 위임하지 않는다.
코드나 템플릿을 복사할 필요가 생기면 판본·출처·라이선스 고지를 유지한다.

성능·비용·문서 품질 우위는 아직 미검증이다. 고정 입력의 실제 모델 평가에서
이를 비교한 뒤 확대 여부를 판단해야 한다. 이번 플랜은 바로 그 평가를 PR별
수용 조건에 넣는다.
