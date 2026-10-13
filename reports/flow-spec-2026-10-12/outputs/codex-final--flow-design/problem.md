---
id: "problem:personal-tag-lookup"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "chain-notes.md"
    revision: "supplied snapshot; revision unknown"
depends_on: []
---

# 문제 정의: 기존 태그로 읽기 노트 찾기

## 사용자와 현재 상황

기존 읽기 노트와 정확한 태그를 가지고 있는 개인 사용자가, 선택한 태그에 해당하는 노트를 찾는 상황이다. 원자료는 합성 평가 입력이며 실제 고객 조사나 측정 자료가 아니다(EV-001).

사용자는 태그로 찾으려 할 때 관련 없는 노트를 반복해서 연다고 보고한다. 현재 우회 방법은 노트 목록을 훑는 것이다(EV-002). 반복 횟수, 소요 시간, 발생 비율은 제공되지 않았다.

## 문제와 원하는 결과

선택한 기존 태그에 해당하는 노트를 구분하기 어려워 관련 없는 노트를 열고 목록을 살펴야 한다는 것이 보고된 마찰이다(EV-002). 사용자가 제안한 도구는 기존 태그를 선택해 해당 태그가 달린 기존 노트만 빠짐없이 찾고, 찾은 노트의 저장된 내용을 여는 것이다(DEC-001). 이는 개인 작업의 원하는 결과이며 시장 수요를 입증하지 않는다.

## 근거와 결정

- EV-001 — SRC-001, 제목 및 첫 문장: “synthetic evaluation request, not measured customer research.” 이 문서의 문제는 제공된 합성 개인 작업 사례로 한정한다.
- EV-002 — SRC-001, “I keep existing reading notes”부터 “scan the note list”까지: 기존 노트/태그, 관련 없는 노트를 반복해서 여는 마찰, 목록 훑기라는 우회 방법이 보고되어 있다. 독립 관찰은 하지 않았다.
- DEC-001 — SRC-001, “returns exactly the existing notes carrying my selected existing tag and lets me open their stored content”: 기존 태그에 따른 정확한 결과와 저장된 내용 열기가 원하는 범위다.
- DEC-002 — SRC-001, “no tag editing, team sharing, new authentication or quantitative speed target”: 태그 편집, 팀 공유, 새 인증, 정량 속도 목표는 제외한다.
- DEC-003 — SRC-001, “An empty lookup must be visibly distinct from a failed lookup”: 결과 없음과 조회 실패를 사용자가 눈으로 구분할 수 있어야 한다.
- DEC-004 — SRC-001, “Do not decide layout, architecture or storage” 및 “design select/open/empty/failure user flows next”: 다음 작업은 선택/열기/결과 없음/실패 흐름 설계이며 레이아웃, 아키텍처, 저장 방식은 여기서 정하지 않는다.
- DEC-005 — SRC-001, 마지막 세 문장: 이 좁은 흐름 범위에는 막힌 제품 정책 결정이 없으며 기존 데이터 읽기 가능성은 추후 확인할 통합 가정이다. 시장 검증이나 측정을 수행했다고 주장하지 않는다.

## 가정과 다음 확인

AS-001 — 기존 노트, 태그 및 저장된 내용을 읽을 수 있다고 가정한다. 이유는 기존 데이터를 활용하는 요청이며, 실제 데이터 접근은 확인하지 않았기 때문이다. 접근할 수 없으면 실제 조회/열기 구현 가능성에 영향을 준다. 통합 검토에서 실제 기존 데이터의 태그 관계와 노트 내용 읽기를 확인한다. 현재의 네 가지 사용자 흐름을 정의하는 데는 비차단 가정이며 새 제품 정책 결정으로 취급하지 않는다(DEC-005). 접근 검증에서 추가 정책 선택이 필요한 제약이 발견되면 해당 근거로 범위를 다시 검토한다.

현재 미해결 제품 결정(OD)은 없다. 제공되지 않은 데이터 형식과 접근 방법은 추후 통합 확인 사항으로 남긴다. 추가 페르소나나 실제 수요를 추정하지 않는다.

## 성숙도와 한계

`ready_for_review`: 개인 작업의 문제, 원하는 결과, 경계가 원자료에 연결되어 검토 가능한 상태다. 실제 사용성, 수요, 속도 또는 데이터 접근을 검증한 상태가 아니며 구현 승인을 의미하지 않는다. 다음 단계의 PRD는 이 범위의 관찰 가능한 동작을 구체화한다.
