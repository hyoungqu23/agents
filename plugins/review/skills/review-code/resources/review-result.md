# Structured review result

Use this contract for Git-backed reviews. Keep the JSON ledger outside the reviewed
checkout; the user-facing answer stays concise. A project gate may retain its own
human report vocabulary; map its evidence to this ledger without changing meaning.
For a pasted patch or non-Git snapshot, report the unavailable Git verification and
do not invent SHAs or claim this mechanical gate passed.

## Capture the real scope before review

Use the trusted installed script. For a PR/branch with a clean checkout at its head:

```sh
python3 /installed/review-code/scripts/review_result.py capture \
  --worktree /reviewer --base BASE_SHA --head HEAD_SHA --output /state/scope.json
```

For local staged, unstaged and untracked changes, use `--working-tree` instead of
`--base`/`--head`. Staged/unstaged changes remain in scope even if they cancel in the
final working copy. Binary and untracked contents are fingerprinted. Keep outputs
outside the source so they do not change the inventory. Capture again after any
authorized autofix and review the resulting changes; never reuse a stale result.

Copy the returned `target` verbatim into the result and account for every entry in
`files`, including renamed/deleted/generated/config/test files. The helper does not
fetch, run tests, execute target code or follow symlinks to read external source.

## Write review-result.json

Required fields:

- `schema_version`: `1`.
- `target`: exact `target` object from capture, including mode, base/head SHA and digest.
- `files`: one entry for every captured path. Each has `path`, `classification`
  (`source`, `test`, `config`, `migration`, `generated`, `lock`, `fixture`, `docs`, `other`),
  `risk` (`low`, `medium`, `high`), `status` (`reviewed`, `unreviewed`, `unresolved`) and
  a concrete `note` about the behavior/decision. High-risk entries also need `trace`
  describing the caller-to-effect path and any open edge. Use `unresolved` for an
  unclosed trace. Missing or unreviewed files make the result partial.
- `passes`: `standards`, `spec`, `runtime`, each with `status` (`complete` or `partial`)
  and a concrete `note`. Spec alone may be `unavailable` with a reason; that leaves
  spec conformance unverified even when the remaining scope can close.
- `quality`: `cohesion`, `coupling`, `duplication`, `repository_fit`, `naming`, each with
  `status` (`checked`, `not_applicable`, `unresolved`) and `note` identifying the changed
  behaviors and relevant searches/owners, or why it does not apply. This summarizes
  the per-behavior ledger; do not replace review with generic checkmarks.
- `verification`: entries with `kind` (`static`, `command`), `status` (`passed`, `failed`,
  `not_run`) and `detail`. Record actual commands only when executed. Failed/not-run
  checks require `reason` and residual `risk`. Honest unavailable runtime checks do
  not prevent recording a completed static scope.
- `findings`: supported findings and excluded/unresolved candidates, using stable IDs.
- `limitations`: text array; may be empty. Do not put silently skipped work only here:
  its file/pass/candidate status must also reflect that gap.
- Optional `review_body`: exact authorized Pending summary. Omit it, and the draft's
  `body`, on continuation to preserve a manually edited summary.

A supported finding has this shape (use actual evidence, never this example as data):

```json
{
  "id": "empty-input",
  "status": "supported",
  "severity": "P1",
  "path": "app.py",
  "line": 2,
  "revision": "head",
  "trigger": "Caller supplies an empty list.",
  "effect": "The documented None result becomes an IndexError.",
  "fix": "Restore the empty-input guard.",
  "refutation": "Inspected callers and the base contract; empty input is accepted.",
  "evidence": [
    {"revision": "head", "path": "app.py", "line": 2, "quote": "    return rows[0][\"name\"]"}
  ],
  "comment": "Exact reviewed and authorized inline comment text."
}
```

Evidence quotations must match the complete indicated line (outer whitespace is
ignored). Use `base` or `head`; local changes may also use `index` or `working`.
The finding anchor itself must have a matching quotation. Include callers, guards,
tests or contracts as additional references when they support the reasoning.
Use the normalized P1/P2/P3 impact scale in this ledger; retain a named project's
own severity label in the human report or additional finding metadata when needed.

Excluded candidates use `id`, `status` and `reason`. Supported alternative statuses
are `disproved`, `unresolved`, `duplicate`, `out_of_scope`, `not_worth_changing`.
Do not attach severity or copy-ready comments to an unresolved claim. A missing
external contract is a review gap, not proof of a defect. Resolved/excluded candidates
never become eligible Pending comments.

## Validate and report the computed result

```sh
python3 /installed/review-code/scripts/review_result.py validate \
  --worktree /reviewer --base BASE_SHA --head HEAD_SHA \
  --result /state/review-result.json --output /state/assessment.json
```

Use the same `--working-tree` mode for local changes. Output paths are new files;
do not overwrite source or old evidence to conceal a failed attempt.

- `complete`: target, coverage and recorded required checks are accounted for.
- `partial`: missing files/checks, unresolved candidates or rejected evidence remain.
  Show the concrete gaps. Supported findings can still be useful independently.
- `invalid`: stale target or invalid result structure; reuse no findings for a save.

Exit 0 means complete; exit 2 returns partial/invalid JSON; exit 1 is an execution
failure. Inspect the JSON rather than treating every nonzero exit as the same issue.
Do not supply a top-level `status` or `complete`; the checker computes them.

`review-pr save` requires `--review-result`, rechecks it against the current source,
and permits only exact eligible finding IDs/anchors/comment text in the draft.
Use each finding ID as the draft comment's `key`. The receipt records
`review_completion` separately from Pending persistence: a saved partial review is
still partial. Confirmed comments may remain Pending while other files await review.

The checker verifies bookkeeping, source identity and quotations. It cannot prove
that the model read every caller, executed a claimed command, chose the right severity,
or reasoned correctly. Model evaluations must test known defects, false positives and
scope omissions from actual outputs; merely loading a skill is not a quality pass.
