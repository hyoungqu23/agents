# Backend Review Lens

Apply this lens when stack detection (SKILL.md Core Workflow step 2) finds a backend server stack — e.g. `pyproject.toml`/`requirements.txt` with FastAPI/Django/Flask, `package.json` with NestJS/Express/Fastify, or a diff dominated by API/service/persistence code. Skip it for pure frontend or non-server changes. Local project gates override it.

Framework-specific checks below use FastAPI (Python/Pydantic) and NestJS (TypeScript/class-validator) vocabulary because those are the most common cases; translate the principle to the detected framework when it differs.

## API-CONTRACT — Endpoint Design and Response Consistency

Principle: an endpoint's contract (status codes, error shape, pagination, idempotency) must be consistent with the rest of the API and safe for independently-deployed clients.

Check:
- Status code semantics (2xx/4xx/5xx correctness, 422 vs 400 conventions), error envelope shape consistency with existing endpoints, pagination/sorting/filter parameter conventions.
- Response models declared and enforced — FastAPI `response_model`/Pydantic return types; NestJS serialization (`ClassSerializerInterceptor`, DTO return types) — so accidental field leaks are impossible.
- Idempotency of retried mutations (PUT vs POST semantics, idempotency keys for payment-like operations), partial-failure semantics of batch endpoints.

FAIL:
- A mutation endpoint can double-apply on client retry with realistic consequences (duplicate records, double side effects).
- Response includes fields not in the declared schema (ORM entity/raw dict returned directly), leaking internal or sensitive fields.
- Error responses for the new endpoint use a different envelope/status convention than the API's established one, breaking client error handling.

WARN:
- Pagination or filtering conventions diverge from sibling endpoints without reason.
- Status codes are technically valid but semantically misleading (200 with error body).

## AUTHZ-SCOPE — Authorization and Tenant Scoping

Principle: every data access must be scoped to the caller's identity and tenant; object IDs from the client are claims to verify, not facts.

Check:
- AuthN/AuthZ enforcement on new/changed routes — FastAPI dependencies (`Depends`), NestJS guards (`@UseGuards`) — including "internal" and websocket/queue-triggered handlers.
- Object-level permission (IDOR): fetching by client-supplied ID verifies ownership/tenant membership before acting.
- Tenant/org filter present in every query touching multi-tenant tables; no trust of client-provided org/user/role fields in request bodies.

FAIL:
- A route performs reads/writes without the auth dependency/guard its siblings use.
- A query looks up by raw client-supplied ID without tenant/ownership scoping, allowing cross-tenant access.
- Role/permission is read from the request payload instead of the server-side session/token.

WARN:
- Authorization exists but is duplicated ad hoc per route instead of using the established dependency/guard pattern, inviting future gaps.

## DB-SAFETY — Query, Transaction, and Consistency Safety

Principle: persistence code must stay correct under concurrency and realistic data volume.

Check:
- N+1 query patterns (ORM lazy loading in loops — SQLAlchemy relationship access, TypeORM/Prisma nested fetches), missing eager-load/join for new access paths.
- Transaction boundaries around multi-step writes; read-check-write races (`SELECT` then `INSERT/UPDATE` without lock/unique constraint); bulk operations bypassing model hooks.
- New query predicates versus existing indexes; unbounded result sets on growing tables.

FAIL:
- Multi-step write lacks a transaction and a realistic mid-failure leaves inconsistent state.
- A read-check-write race can create duplicates or violate an invariant that a unique constraint/lock should protect.
- A hot-path query is unbounded or unindexed with realistic table growth, predictably degrading the endpoint.

WARN:
- N+1 exists but on an admin/low-volume path; recommend eager loading.
- Transaction exists but spans external I/O (HTTP calls inside DB transactions), holding locks across network latency.

## INPUT-VALIDATION — Request Validation at the Edge

Principle: every request surface (body, query, path, headers, files) is parsed through the framework's validation layer before use.

Check:
- FastAPI: Pydantic models for bodies, typed `Query`/`Path` params, no raw `dict`/`Request.json()` passthrough. NestJS: DTOs with class-validator + global `ValidationPipe` (whitelist), no `any`-typed `@Body()`.
- Numeric/string bounds (lengths, ranges, enum membership), file upload size/type limits, collection size caps on batch endpoints.
- Consistency with the deeper TRUST-BOUNDARY criterion in the common gate: this lens checks the framework mechanism; common gate checks what unvalidated data can reach.

FAIL:
- A new endpoint accepts an unvalidated raw body/params and uses it in persistence, queries, or business decisions.
- Validation is declared but bypassed (manual JSON parsing, `any` casts, disabled pipes) on the changed path.

WARN:
- Validation exists but bounds are absent where realistic abuse exists (unbounded batch arrays, unlimited string lengths on indexed columns).

## FAILURE-CONTRACT — Error Handling and External Integration

Principle: failures must surface with correct semantics — never silently converted into success — and external calls must assume the dependency will misbehave.

Check:
- Broad `except`/`catch` blocks on changed paths: do they log-and-rethrow with proper status, or swallow and return default/200?
- External calls (HTTP, queue, storage, LLM): timeout set, failure path defined, retry with backoff where safe (and idempotent), no unbounded retries.
- Logs on error paths include correlation context but not secrets/tokens/PII; background jobs and consumers surface failures (dead-letter/alert) instead of crashing silently or infinitely retrying poison messages.

FAIL:
- An exception path returns a success response or default data, hiding the failure from clients and monitoring.
- A new external call has no timeout on a request-serving path, letting a slow dependency exhaust workers.
- Secrets/tokens/PII are written to logs on the changed path.

WARN:
- Failure is surfaced but with a generic 500 where the established envelope distinguishes error kinds.
- Retry exists without backoff/jitter or wraps a non-idempotent operation.

## Evidence Requirements

- AUTHZ-SCOPE / DB-SAFETY findings need the actual route/query path (route decorator → handler → query) — not just a grep match.
- API-CONTRACT findings should cite the sibling endpoint or convention being diverged from.
- INPUT-VALIDATION findings should cite the unvalidated surface and the sink it reaches.
- FAILURE-CONTRACT external-call findings should cite the call site and the missing control (timeout/retry/error mapping).
