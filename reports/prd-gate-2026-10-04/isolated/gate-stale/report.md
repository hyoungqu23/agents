# 제품 요구사항 검토

**판정: revise. 과거 판정: stale, 재사용 불가.**

broken-prd.md 전체 요구사항의 사용자 흐름 설계 준비도; clean-source.md를 요청과 제외 범위의 근거로 검토

## 대상과 입력

- 대상: `broken-prd.md`, ID `prd:personal-tag-finder`, revision 2, status `ready_for_review`.
- 대상 SHA-256: `9bb4c6a75b761a44bdfb2d0d924f2e81aa6940e9f47e77103e4937d708015244`
- 선언된 depends_on: 없음. 원문은 SRC-001로 참조됨.
- 읽은 입력: `clean-source.md` — SRC-001; PRD 기재 supplied snapshot 1; 원문 자체 ID/revision은 unknown; SHA-256 `34e48200e92d3502e8e33f109af7ac6bb57c0652af761d8232b7e2320f1fce57`.
- 읽은 입력: `prior-review.json` — 과거 검토; 보고서 자체 ID/revision 및 검토 시점 unknown; SHA-256 `844a65f244a0d1cf7b9e649710c16bb1e18bc8b3e4d566d14bd3066258de6b20`.

## 과거 판정의 신선도

ID와 revision 2는 같지만 현재 대상 SHA-256이 과거 기록과 다르다. 과거 ready_for_flow를 현재 판본에 재사용할 수 없다. 과거 보고서에는 원문/의존성 식별 정보가 없어 원문의 과거 대비 변경 여부도 검증할 수 없다. 현재 입력은 새로 검토했다.

과거 대상 SHA-256: `5c52a29994694dd36dcd9a013c438628993e9ccb49f84b3d7e7362539f7b76dd`. 과거 findings는 빈 목록이므로 재검증할 개별 지적은 없다. 과거 전체 판정을 현재 판본에 승계하지 않았다.

## R1–R5 검토

- **R1 — assessed**: 원문은 개인 소유자의 워크플로 요청이다. EV-001의 정확한 태그 검색 근거를 확인했다. 시장 수요나 실측 성과를 입증한 자료로 해석하지 않았다.
- **R2 — assessed**: 개인 사용자와 찾기·열기 결과를 대조했다. 열기 결과 누락(F-004)과 외부 사용자 확대(F-001)를 확인했다.
- **R3 — assessed**: 요구와 AC 전체를 확인했다. 관찰 불가능한 AC(F-002), 빈 결과·조회 실패 구분 누락(F-003)을 확인했다.
- **R4 — assessed**: 공유 제외와 공개 열람의 충돌(F-001)을 확인했다. 태그 편집·새 인증 제외는 원문의 제약으로 유지한다. UI·저장소 결정과 속도 수치는 전제하지 않는다.
- **R5 — assessed**: 대상 ID/revision, 실제 바이트 해시와 과거 해시를 비교했다. 동일 revision에서 해시가 달라 과거 판정은 stale이다. 과거 원문 의존성 해시는 제공되지 않았다.

## 확인된 지적

### F-001 · R4 · confirmed

위치: broken-prd.md:17–18 / FR-003, AC-003

근거:
- FR-003: Anonymous external users can read every stored note by a public link.
- broken-prd.md:13 / DEC-001: Personal use only; sharing and new authentication are excluded.
- clean-source.md:3–4: Personal use only; exclude tag editing, sharing and new authentication.

흐름 설계 영향: 개인용 탐색 범위에 외부 익명 열람 흐름이 섞인다. 모든 요구사항의 흐름 설계(19행)를 그대로 진행할 수 없다.

수정 방향: 공개 링크 요구사항을 명시된 개인용·공유 제외 결정과 일치시키도록 수정한다. 공유를 새 결정으로 채택하지 않는다.

### F-002 · R3 · confirmed

위치: broken-prd.md:16 / AC-001

근거:
- AC-001: Search feels good.
- clean-source.md:2: find and open existing reading notes using their exact existing tags.

흐름 설계 영향: 검색 결과가 요구를 충족하는지 관찰하여 판단할 수 없어 성공 흐름의 완료 조건을 정할 수 없다.

수정 방향: 기존 태그의 정확한 일치로 해당 노트를 찾는 등 원문에 근거한 관찰 가능한 수용 기준을 기록한다. 합의되지 않은 속도 수치는 추가하지 않는다.

### F-003 · R3 · confirmed

위치: broken-prd.md:14–18 / GOAL-001, FR-001 및 전체 AC

근거:
- GOAL-001: Find notes by selected tag. / FR-001: Search selected tags.
- broken-prd.md:16–18의 AC는 주관적 검색 평가와 공개 링크 열람만 다룬다.
- clean-source.md:4: Empty lookup and failed lookup must be distinguishable.

흐름 설계 영향: 결과 없음과 조회 실패가 구분되지 않아 빈 상태와 실패 상태의 사용자 흐름을 요구사항에 근거해 분기할 수 없다.

수정 방향: 빈 조회 결과와 조회 실패를 사용자가 구별할 수 있다는 요구 및 관찰 가능한 수용 기준을 복원한다. 화면 배치나 구현 방식을 정하지 않는다.

### F-004 · R2 · confirmed

위치: broken-prd.md:12,14–18 / EV-001, GOAL-001, FR-001

근거:
- EV-001: The owner requests finding existing reading notes by exact tags.
- GOAL-001과 FR-001은 찾기/검색까지만 명시한다.
- clean-source.md:2: find and open existing reading notes using their exact existing tags.
- broken-prd.md:17–18의 열람은 제외된 외부 공개 링크에 한정된다.

흐름 설계 영향: 개인 사용자가 찾은 기존 노트를 여는 핵심 결과가 빠져 검색 후 열람까지의 정상 흐름이 완결되지 않는다.

수정 방향: 개인 사용자가 검색한 기존 노트를 여는 요구와 완료 조건을 원문에 맞게 명시한다.

## 열린 결정과 미확인 주장

추가 제품 결정이 필요한 항목은 확인되지 않았다. 공개 공유는 원문의 명시적 제외 사항이므로 열린 선택으로 재분류하지 않는다. 확인 불가능한 개별 증거 질문 및 반박할 과거 개별 지적도 없다. clean-source.md 자체에서는 다음 흐름 설계를 막는 모순을 발견하지 않았다. 숫자 속도 목표와 시장 조사의 부재는 결함이 아니다.

## 다음 단계와 한계

정확한 기존 태그로 개인 노트를 찾는 흐름의 범위는 파악할 수 있다. 전체 흐름 확정은 F-001~F-004 수정 및 재검토 후 진행해야 한다. 빌드/배포 승인이 아니다.

unverified — 저자 및 검토 호출 이력이 제공되지 않아 독립성을 확인할 수 없다.

- 제공된 로컬 문서만 검토했다. 실제 제품 동작, 시장 수요 및 성능은 평가하지 않았다.
- 과거 대상의 실제 바이트와 과거 원문 해시가 없어 변경 내역 전체와 의존성 신선도를 재구성할 수 없다. 현재 검토를 막는 필수 입력 누락은 없다.
- UI 배치, API, 데이터 저장소 및 구현 설계는 검토 범위 밖이다.

적용 기준:
- `.eval-plugins/product/skills/prd-gate/SKILL.md`
- `.eval-plugins/product/references/artifact-contract.md`
- `.eval-plugins/product/references/prd-review-contract.md`

입력 원본과 스킬 소스는 수정하지 않았다.
