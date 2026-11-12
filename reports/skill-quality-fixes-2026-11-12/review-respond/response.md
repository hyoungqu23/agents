# 오프라인 리뷰 처리 결과

PR `acme/invoice-app#88`, 브랜치 `feat/invoices`에서 빈 성공 응답 수정과 회귀 테스트를 완료했다. 로컬 커밋: `69706c5348193aa9bd62c54ac19cff33bff871d2`. 작업 트리는 깨끗하다. push와 답글 게시, resolve, 재검토 요청은 하지 않았다.

## 처리한 스레드

### [fix] @dana — src/invoices.mjs:4 (T1)

- 요청: “빈 배열 응답이 정상인데 첫 항목의 status를 읽으면서 예외가 납니다. 빈 성공도 처리해 주세요.”
- 확인: `contract.md:5`는 빈 배열을 정상 입력으로 정의한다. 기존 `items[0].status` 접근은 `summarizeInvoices([])`에서 TypeError를 발생시켰다.
- 변경: `69706c5` — 빈 배열이면 `{ count: 0, firstStatus: null }`을 반환한다. 기존 비어 있지 않은 입력의 동작은 유지한다.
- 답글: 아래 초안 1, 미게시.

### [fix] @dana — PR #88 리뷰 본문 (줄 없음)

- 요청: CHANGES_REQUESTED — “빈 성공의 회귀 테스트도 추가해 주세요.”
- 확인: 기존 테스트는 비어 있지 않은 응답만 검증했다.
- 변경: `69706c5` — `tests/invoices.test.mjs:10`에 빈 성공 결과 전체를 확인하는 테스트를 추가했다.
- 답글: 아래 초안 2, 미게시. 원본 리뷰 ID는 스냅샷에 없다.

## 정확한 답글 초안

1. T1 / @dana / `fix` / `69706c5` — 원래 인라인 스레드에 게시할 초안:

```markdown
빈 성공 응답에서 `{ count: 0, firstStatus: null }`을 반환하도록 수정했습니다. 빈 배열 회귀 테스트와 기존 응답 테스트 2개가 통과했습니다. [69706c5](https://github.com/acme/invoice-app/commit/69706c5348193aa9bd62c54ac19cff33bff871d2)
<!-- review-respond -->
```

2. 리뷰 본문 / @dana / `fix` / `69706c5` — 대화 코멘트로 게시할 초안:

```markdown
@dana
> 빈 성공의 회귀 테스트도 추가해 주세요.

`tests/invoices.test.mjs`에 빈 배열의 결과가 `{ count: 0, firstStatus: null }`인지 확인하는 테스트를 추가했습니다. 수정 전에는 TypeError로 실패했고, 수정 후에는 기존 테스트를 포함해 2개 모두 통과했습니다. [69706c5](https://github.com/acme/invoice-app/commit/69706c5348193aa9bd62c54ac19cff33bff871d2)
<!-- review-respond -->
```

## 보류

- [defer] T2 / @dana / `src/invoices.mjs:1`: “프로덕션 목록이 느립니다. v2 API로 전환해야 하지 않나요?” `contract.md:3`의 DEC-12는 소유자가 v2 전환을 거절한 기존 결정이며, 로컬에 프로덕션 프로파일링도 없다. 성능 주장과 v2의 해결 효과는 미확인이다. 재검토에는 새 소유자 결정과 병목·v2 효과를 확인할 성능 근거가 필요하다. `/v1/invoices`를 유지했고 이 항목의 답글은 작성하지 않았다. 파서 계약은 API 버전과 독립적이므로 이 보류는 T1과 회귀 테스트를 막지 않는다.

## 리뷰어 대기

- 없음. 인라인 스레드 2개 모두 마지막 작성자가 dana이다.

## 검증

- 대상: 제공된 `review.md`만 사용. 인라인 2개, 리뷰 본문 1개, 대화 0개; 스냅샷상 내 차례인 항목 3개 중 2개 처리, 1개 보류. `viewer hm2`, `viewerDidAuthor true`, `CHANGES_REQUESTED`는 제공된 메타데이터이며 원격 재검증은 하지 않았다.
- 리비전: 시작 로컬 HEAD `a23a9f252c6aaaf10744c581a669b36e3121ce61` → 수정 HEAD `69706c5348193aa9bd62c54ac19cff33bff871d2`. 원본 리뷰 리비전과 원격 head SHA는 스냅샷에 없어 알 수 없다.
- `npm test` (회귀 테스트 추가 후, 수정 전): 1개 통과, 1개 TypeError 실패로 T1 재현. 같은 명령을 수정 후 실행: 2개 통과. `git diff --check`: 통과. `git status --short`: 출력 없음.
- `content:un-ai` Edit 패스: 허용된 작업 범위에 해당 플러그인이 없어 미실행. 짧은 문장, 정확한 식별자, 군더더기 없는 표현이라는 스킬의 직접 제약을 적용했다.
- 게시 상태: 미push, 답글 0건, resolve 없음, 재요청 없음. 커밋 링크는 push 후 열 수 있다. 실제 게시 전 최신 원격 head·답글과 원본 노드 ID 확인이 필요하다. T1/T2는 스냅샷 별칭이며 실제 GraphQL ID로 간주하지 않는다.
- 상태 기록: 게시하지 않았으므로 처리 완료 영수증이나 `repliedAt`을 만들지 않았다. 이 파일을 오프라인 결과와 초안으로 보관한다.
