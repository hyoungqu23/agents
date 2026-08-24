# Review Execution Harness

Use this resource for every review. It defines the internal bookkeeping and completion conditions that prevent an evidence-first report from becoming a narrow spot check.

## 1. Establish Scope and Intent

Record the target identity before reading for defects:

- PR/MR URL or number, repository, base ref, head ref, and head commit when available
- branch, commit range, patch, or working-tree state when there is no PR
- authoritative intent sources: user prompt, PR title/body, linked issue, acceptance criteria, PRD, plan, commit messages, and relevant docs
- unavailable sources and the reason they could not be read

Build one canonical changed-file inventory. For a PR, reconcile the host's file list with the diff actually reviewed. For a working tree, combine staged, unstaged, and untracked lists. Include additions, modifications, deletions, renames, generated files, lockfiles, tests, configuration, migrations, fixtures, and docs.

Do not equate "not hand-written production code" with "out of scope." Classify every file. A generated or lockfile change can be low-risk, but it can also prove an unintended dependency or build change.

## 2. Maintain the Coverage Ledger

Keep the ledger internal unless the user asks to see it. Use one row per changed file and link rows that implement the same changed behavior.

Minimum fields:

| Field | Record |
| --- | --- |
| File and changed lines | Repository-relative path, status, and reviewed hunks |
| Classification | Source, test, config, migration, generated, lock, fixture, docs, or other |
| Risk | High, medium, or low with a concrete reason |
| Changed behavior | What user-visible or system behavior this file participates in |
| Callers and consumers | Entry points, direct callers, downstream readers, separately deployed consumers |
| External contract | API, schema, persistence, auth, event, file, environment, UI, or third-party boundary |
| Requirement | Intent source and requirement identifier, or "spec unavailable" |
| Verification | Existing/changed tests and commands that exercise the behavior |
| Candidates | Candidate IDs raised while reviewing this row |
| Disposition | Reviewed with no candidate, promoted, disproved, duplicate, out of scope, or unresolved |

Risk guidance:

- High: auth/tenant scope, money, destructive writes, irreversible data change, migration or deploy ordering, concurrency, trust boundaries, public API/schema changes, secrets, or broad shared infrastructure.
- Medium: product behavior, error/fallback paths, caching/state, non-destructive persistence, shared components/utilities, performance-sensitive paths, or meaningful config changes.
- Low: isolated mechanical changes, docs, snapshots, or generated output with no detected behavioral contract. Low risk still requires classification and review.

When several files implement one behavior, create a behavior note that connects its entry point, transformations, boundaries, effect, tests, and deployment implications. This avoids reviewing each file in isolation.

## 3. Discover Before Filtering

Run all three passes over the full inventory. Candidate discovery is intentionally broad; do not apply the evidence threshold until the passes are complete.

### Standards Pass

- Compare with repository instructions, architecture, naming, ownership, nearby patterns, lint/type configuration, and installed framework idioms.
- Look for divergence that creates a concrete maintenance or correctness cost, not stylistic preference alone.

### Spec Pass

- Turn every available acceptance criterion or promised behavior into a small checklist.
- Map each item to implementation and a test, or create a candidate for the gap.
- For refactors, identify old behavior and prove it remains unless the intent explicitly changes it.
- Note scope added by the diff that is not explained by the intent source.

### Runtime Contract Pass

- Follow data and control flow through runtime validation, narrowing, transformation, async work, state/cache updates, persistence, external calls, rendering, and recovery paths.
- Check both success and failure states, including empty, partial, duplicate, stale, unauthorized, retried, cancelled, and concurrently changed inputs when relevant.
- Compare both sides of a boundary: writer/reader, server/client, producer/consumer, old/new deployment, parser/type, or migration/application.

Each candidate note should contain:

- pass and candidate ID
- smallest plausible anchor
- triggering condition
- concrete observable effect
- suspected broken contract or requirement
- smallest useful fix or verification
- evidence for and against the hypothesis
- current disposition

## 4. Trace High-Risk Behavior

Use this trace shape and adapt it to the stack:

```text
entry/caller -> validation -> transformation/state -> trust or process boundary
             -> sink (render/write/call/emit) -> observable effect -> recovery/test
```

Examples:

- UI: route or event -> hook/state -> request/cache -> render states -> accessibility and recovery
- API: route -> authentication/authorization -> validation -> service -> database/external call -> response/error contract
- Async: producer -> ownership/cancellation -> ordering/retry -> shared state -> completion/error observation
- Persistence: input -> transaction/constraint -> write -> reader/query -> rollback or retry behavior
- Release: old/new producer and consumer combinations -> migration/config/flag ordering -> rollback path

For every high-risk behavior, inspect the changed code plus the callers, consumers, and tests needed to reach an observable effect. If access or scale prevents the trace from closing, mark it unresolved and explain the exact missing edge.

## 5. Refute and Dispose Candidates

Try to disprove every candidate before promotion:

- inspect guards, call-site preconditions, runtime schemas, feature flags, transactions, error boundaries, and cleanup paths
- search for all relevant callers/consumers and alternate implementations
- read tests for the claimed trigger and effect, not merely similarly named tests
- compare local conventions and installed versions
- distinguish behavior introduced by the target from pre-existing behavior

Promote only when all are true:

1. The trigger is reachable or the violated contract is authoritative.
2. The effect is concrete and material enough for the chosen severity.
3. The issue belongs to the reviewed target or is directly exposed by it.
4. A smallest useful fix or verification can be stated.
5. A valid `file:line` anchor exists.

Use one terminal disposition per candidate:

- `promoted`: becomes one finding
- `disproved`: evidence shows the failure cannot occur
- `duplicate`: covered by another candidate; retain one canonical finding
- `out of scope`: unrelated pre-existing issue; mention only if needed to explain verification
- `unresolved`: insufficient contract or runtime evidence; report as residual risk, not as a proven finding

For absence findings, anchor the production branch, contract declaration, test script, or nearest changed line where the missing behavior becomes actionable. Never invent a line outside the evidence.

## 6. Completion Gate

Do not present the review as complete until all checks pass:

- the canonical inventory includes every PR, staged, unstaged, and untracked file
- every file has classification, risk, changed behavior, and a terminal disposition
- every high-risk behavior has a closed caller-to-effect trace or an explicit unresolved edge
- every known requirement maps to implementation, test, or a promoted gap
- every candidate has exactly one terminal disposition
- relevant verification commands ran, or each skipped command has a concrete reason and residual risk
- autofixes, if any, were re-diffed and re-entered into the ledger
- no generated, deleted, renamed, test, config, migration, or documentation file was silently ignored

For large diffs, review in batches and track batch completion in the same ledger. Time or context pressure is a reason to report an incomplete scope, not a reason to imply that unreviewed files passed.

If spec evidence is unavailable, the completion gate can still close for scope and runtime review, but the final verification section must say that spec conformance was not established.
