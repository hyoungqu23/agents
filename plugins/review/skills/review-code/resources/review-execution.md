# Review Execution Harness

Use this resource for every review. It owns scope, bookkeeping, discovery, candidate handling, and completion; criterion definitions and Change Restraint live in `common-gate.md`, and verification rules in `verification-matrix.md`.

## 1. Establish Scope and Intent

Record the target identity before reading for defects:

- PR/MR URL or number, repository, base ref, head ref, and head commit when available
- branch, commit range, patch, or working-tree state when there is no PR
- authoritative intent sources: user prompt, PR title/body, linked issue, acceptance criteria, PRD, plan, commit messages, and relevant docs
- unavailable sources and the reason they could not be read

Build one canonical changed-file inventory. For a PR, reconcile the host's file list with the diff actually reviewed. For a working tree, combine staged, unstaged, and untracked lists. Include additions, modifications, deletions, renames, generated files, lockfiles, tests, configuration, migrations, fixtures, and docs.

Do not equate "not hand-written production code" with "out of scope." Classify every file. A generated or lockfile change can be low-risk, but it can also prove an unintended dependency or build change.

## 2. Maintain the Coverage Ledger

Keep the ledger out of the concise user-facing answer unless requested. For Git-backed
reviews, persist it with [the structured result contract](review-result.md) outside
the reviewed checkout and run its checker. Use one row per changed file and link rows
that implement the same changed behavior.

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
| Engineering quality | Per changed behavior: cohesion, coupling, duplication, repository/BP fit, and naming dispositions; existing-implementation search terms/locations and relevant owners/counterparts, or an explicit inapplicable/unresolved reason |
| Verification | Existing/changed tests and commands that exercise the behavior |
| Candidates | Candidate IDs raised while reviewing this row |
| Disposition | Reviewed with no candidate, promoted, disproved, not worth changing, duplicate, out of scope, or unresolved |

Risk guidance:

- High: auth/tenant scope, money, destructive writes, irreversible data change, migration or deploy ordering, concurrency, trust boundaries, public API/schema changes, secrets, or broad shared infrastructure.
- Medium: product behavior, error/fallback paths, caching/state, non-destructive persistence, shared components/utilities, performance-sensitive paths, or meaningful config changes.
- Low: isolated mechanical changes, docs, snapshots, or generated output with no detected behavioral contract. Low risk still requires classification and review.

When several files implement one behavior, create a behavior note that connects its entry point, transformations, boundaries, effect, tests, and deployment implications. This avoids reviewing each file in isolation.

## 3. Discover Before Filtering

Run all three passes over the full inventory. Candidate discovery is intentionally broad; do not apply the evidence threshold until the passes are complete.

### Standards Pass

- Apply all five Engineering Quality criteria from `common-gate.md` to each changed behavior using repository authority and version evidence selected through `skill-routing.md`. Record the required existing-implementation search in the ledger.

### Spec Pass

- Map each requirement to implementation and verification, or a gap candidate, using SPEC-COVERAGE in `common-gate.md` and Regression Sensitivity in `verification-matrix.md`.
- For refactors, establish old behavior and preserve it unless explicitly changed; record scope additions not explained by intent.

### Runtime Contract Pass

- Follow data and control flow through runtime validation, narrowing, transformation, async work, state/cache updates, persistence, external calls, rendering, and recovery paths.
- Check both success and failure states, including empty, partial, duplicate, stale, unauthorized, retried, cancelled, and concurrently changed inputs when relevant.
- Apply ASYNC-SAFETY in `common-gate.md` to async lifetimes and partial writes, recording its required trace in the behavior note.
- Compare both sides of a boundary: writer/reader, server/client, producer/consumer, old/new deployment, parser/type, or migration/application.

Each candidate note should contain:

- pass and candidate ID
- smallest plausible anchor
- triggering condition, or the current responsibility/dependency/rule/name at issue
- concrete observable effect or demonstrated maintenance cost, with corroborating owner, counterpart, convention, or caller
- basis and actual source of the suspected broken contract, requirement or recommendation, and why its scope applies
- smallest useful fix or verification
- change restraint: cost of leaving the code, smallest complete remedy, and benefit versus complexity/compatibility/regression cost; relevant prior decision if any
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

1. The trigger is reachable, the violated contract is authoritative, or the structural defect is demonstrated by the changed code and its relevant owners/consumers.
2. The effect is concrete and material enough for the chosen severity.
3. The issue belongs to the reviewed target or is directly exposed by it.
4. A smallest useful fix or verification can be stated.
5. A valid `file:line` anchor exists.
6. The proposed remedy passes the Change Restraint gate in `common-gate.md`; maintainability-only cleanup without demonstrated net benefit is excluded.

Use one terminal disposition per candidate:

- `promoted`: becomes one finding
- `disproved`: evidence shows the failure cannot occur
- `not worth changing`: no concrete present cost, or the maintainability benefit does not justify the remedy; briefly explain if shown under excluded items
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
- all five engineering-quality criteria have a disposition per changed behavior, with existing-implementation search evidence or an explicit inapplicable/unresolved reason
- every candidate has exactly one terminal disposition
- every promoted finding exposes its basis, inspected or supplied source, applicability and required versus optional change under `common-gate.md#finding-basis`
- relevant verification commands ran, or each skipped command has a concrete reason and residual risk
- autofixes, if any, were re-diffed and re-entered into the ledger
- no generated, deleted, renamed, test, config, migration, or documentation file was silently ignored

For large diffs, review in batches and track batch completion in the same ledger. Time or context pressure is a reason to report an incomplete scope, not a reason to imply that unreviewed files passed.

If spec evidence is unavailable, the completion gate can still close for scope and runtime review, but the final verification section must say that spec conformance was not established.

Use the checker's computed result for Git-backed scope and evidence consistency.
Missing files or incomplete recorded checks remain partial even when a supported
finding is saved as Pending. Do not substitute a skill-read event or a successful
GitHub write for completed review work. Semantic quality still requires evidence-based
judgment; a mechanically valid JSON ledger is not proof of that judgment.
