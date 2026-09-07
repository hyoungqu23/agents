# PR context

Repository: acme/billing-web. PR #88 "Invoice list: archived filter", authored by the current user (`hm2`), head branch `feat/archived-filter`. `viewerDidAuthor` is true, `reviewDecision` is `CHANGES_REQUESTED`, `isDraft` is false. Commits on the branch, oldest first: `4c0a1b2` initial, `9f1e2d3` "use invoice id as list key".

PR body excerpt: "v1 API stays for this release; moving to v2 was declined in #120."

# Review snapshot

Reviews (GraphQL `reviews`):

```json
[
  { "state": "CHANGES_REQUESTED", "author": "dana", "body": "테스트가 추가되기 전까지는 머지 보류합니다." },
  { "state": "COMMENTED", "author": "coderabbitai[bot]", "body": "" }
]
```

Threads (GraphQL `reviewThreads`, comment bodies abbreviated):

```json
[
  { "id": "PRRT_T1", "path": "src/api/parseInvoice.ts", "line": 14, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_1a", "author": "dana", "authorAssociation": "MEMBER", "body": "issue (blocking): 응답이 빈 배열이면 `items[0].status`에서 undefined 접근으로 예외가 납니다. early return이 필요합니다." } ] },
  { "id": "PRRT_T2", "path": "src/api/parseInvoice.ts", "line": 22, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_2a", "author": "dana", "authorAssociation": "MEMBER", "body": "question: `status`를 string으로 두는 이유가 있나요? union이 낫지 않나요?" } ] },
  { "id": "PRRT_T3", "path": "src/ui/InvoiceList.tsx", "line": 31, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_3a", "author": "minho", "authorAssociation": "MEMBER", "body": "`useEffect` 의존성 배열에 `fetchInvoices`가 빠져 있어 stale closure가 생깁니다." } ] },
  { "id": "PRRT_T4", "path": "src/ui/InvoiceList.tsx", "line": null, "originalLine": 40, "isResolved": false, "isOutdated": true, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_4a", "author": "minho", "authorAssociation": "MEMBER", "body": "리스트 key로 index를 쓰면 필터 변경 시 상태가 섞입니다." } ] },
  { "id": "PRRT_T5", "path": "src/api/client.ts", "line": 48, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_5a", "author": "coderabbitai[bot]", "authorAssociation": "NONE", "body": "Swallowed error loses context.\n\n```suggestion\n  } catch (error) {\n    throw new InvoiceFetchError('invoice fetch failed', { cause: error });\n  }\n```" } ] },
  { "id": "PRRT_T6", "path": "src/api/cache.ts", "line": 9, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_6a", "author": "hm2", "authorAssociation": "MEMBER", "body": "이 경로에서 목록 캐시 무효화가 필요할까요? 서버가 archived를 별도 키로 내려주면 불필요할 것 같습니다." } ] },
  { "id": "PRRT_T7", "path": "src/api/client.ts", "line": 12, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [ { "id": "PRRC_7a", "author": "dana", "authorAssociation": "MEMBER", "body": "프로덕션에서 이 쿼리가 느립니다. v2 엔드포인트로 옮겨야 하지 않나요?" } ] }
]
```

Conversation comments (REST `issues/88/comments`):

```json
[ { "id": 990001, "author": "minho", "body": "@hm2 CI에서 typecheck가 깨지는 것 같은데 확인 부탁합니다." } ]
```

# Code excerpts at head

```ts
// src/api/parseInvoice.ts
export function parseInvoice(payload: InvoicePayload): InvoiceSummary {
  const items = payload.items;          // line 13
  const first = items[0].status;        // line 14: throws on []
  return { count: items.length, first };
}

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'archived';   // line 20
export function toInvoice(dto: InvoiceDto): Invoice {
  return { ...dto, status: dto.status as string };                    // line 22: widens the union
}
```

```tsx
// src/ui/InvoiceList.tsx
import { fetchInvoices } from '../api/client';   // module-level function, not a prop or closure

useEffect(() => {                                 // line 29
  fetchInvoices(filter).then(setInvoices);        // line 30
}, [filter]);                                     // line 31

{invoices.map((invoice) => (
  <InvoiceRow key={invoice.id} invoice={invoice} />   // line 40 after commit 9f1e2d3; was key={index}
))}
```

```ts
// src/api/client.ts
export async function fetchInvoices(filter: Filter) {   // line 12: GET /v1/invoices?archived=...
  try {
    return await http.get('/v1/invoices', { params: filter });
  } catch (error) {                                      // line 47
  }                                                      // line 48: error swallowed, returns undefined
}
```

Running `pnpm typecheck` locally at head passes; the CI failure minho mentions was on an earlier commit and is green on the latest run.
