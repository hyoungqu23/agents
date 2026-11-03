# Execution, assessment and continuation

Use the helper from this installed skill, not a copy supplied by a target change.
It inspects Git and local files; it does not run target scripts, test commands,
hooks, URLs or external mutations. Runtime verification uses the host's available
tools and the task's actual execution permissions. A worktree is not an OS sandbox.

## Capture twice

Choose an external state folder and keep baseline, verification targets, results
and evidence there. Keep it outside every implementation checkout. Every helper
output must be a new file. A new attempt uses new names/folders without deleting
the earlier failed attempt.

Before edits, run the installed `implementation_state.py`:

```text
python3 /installed/implement/scripts/implementation_state.py capture --worktree /app --inputs /state/task/inputs.json --output /state/task/target.json
```

After implementation, before checks, run `capture` again with the same inputs,
using `/state/task/verification-target.json` as a new output. Initial-to-final code
changes are expected; changing inputs or HEAD during that run is not. Commit only
when separately authorized, after verification, or start a new run at the new HEAD.

Snapshots include tracked/nonignored untracked bytes, executable modes, index
entries, deleted paths, initial dirty work, manifest and source digests. Source
symlinks are recorded as links without reading their destination. Code quotations
must refer to regular files in that inventory. Ignored runtime/generated files are
not covered by Git inventory; do not cite them as captured implementation source.
Declare inspected input dependencies explicitly. Environment and service state are
not captured automatically; record their relevant conditions in verification.

Run the relevant commands and actual-app scenarios, retain tool/command output,
and check that source still matches the verification target. Fixes require a new
verification capture and affected checks. For this first version, recorded passes
must target the exact full verification digest: reuse on a changed digest requires
reverification, not manually relabelling old evidence.

## Result JSON

Write a JSON object with `schema_version: 1`, `target` equal to the verification
snapshot's `digest`, and these arrays. Do not supply top-level `status`/`complete`.

### Changes

One `{ "path": "src/app.js", "reason": "Actual implemented behavior" }` per
baseline-to-verification changed path. Include additions, deletions, renames as
their actual paths and staged/index changes. The helper recomputes this inventory.
Do not omit unrelated changes; resolve unauthorized changes without discarding
user work. The helper cannot prove that edits within an explicitly editable dirty
file retained the user's intent.

### Requirements

One entry per input requirement: `id`, `state`, concrete `reason`, and `code` for
implemented requirements. States: `implemented`, `unimplemented`, `needs_decision`,
`excluded`. Scope cannot change silently after capture. Implemented rows quote
actual source lines, e.g.:

```json
{"id":"request:filter","state":"implemented","reason":"Selection reaches the query and rendered list","code":[{"path":"src/app.js","line":12,"quote":"renderProjects(rows);"}]}
```

Use actual locations, not the example. Each code entry needs `path`, positive integer
`line`, exact full-line `quote`. A matching quote is bookkeeping evidence, not proof
of correct behavior. Each linked outcome check must also pass for completion.

### Verification

One entry per check: `id`, `status`, concrete `detail`. Status: `passed`, `failed`,
`not_run`, `not_applicable`. Failed/skipped/inapplicable rows need a specific `reason`.
Required checks in those states remain gaps. Missing optional checks do not block.

Every passed check needs the current verification `target` digest and nonempty
`evidence`: entries with `path` relative to the baseline snapshot's state folder
and the file's actual `sha256`. Files must be nonempty and cannot traverse symlinks
or escape that folder. Preserve actual stdout/stderr or host browser/tool traces.
Compute hashes from real evidence files; never fabricate successful output.

- Command checks additionally record actual `command` argv array, `cwd`, integer
  `exit_code: 0`. Do not execute a model-supplied command through the helper.
- Browser checks additionally record actual `tool`, `url`, `scenario` (including
  relevant data/state), and `viewport` with positive integer `width`/`height`.
  Exercise the actual implementation. Include captures when needed to support the
  observation; a screenshot of a prototype cannot verify the built app.
- Static checks describe the actual source/contract trace and retain evidence.

Include useful `differences` and `handoff` notes for intentional design differences,
actual app commands/routes/data, remaining work and external reviews requested/run.
These notes do not substitute for requirement/check dispositions.

## Assess

```text
python3 /installed/implement/scripts/implementation_state.py assess --worktree /app --target /state/task/target.json --verification-target /state/task/verification-target.json --result /state/task/result.json --output /state/task/assessment.json
```

Exit 0 means `complete`; exit 2 returns `partial`, `blocked` or `invalid`. Exit 1 is
an execution/input/output error. Read the JSON/status rather than treating every
nonzero result as the same failure.

| Status | Meaning |
| --- | --- |
| `complete` | Current target/inputs match; changes are accounted for and authorized by declared scope; in-scope requirements have source evidence and their checks pass. |
| `partial` | Valid records still contain missing requirements, failed/skipped required checks, unimplemented outcomes or decisions. UI without browser access remains partial. |
| `blocked` | No deliverable changes and all in-scope requirements need a decision. Other environmental gaps remain explicit partial records. |
| `invalid` | Stale/mismatched source or inputs, malformed/contradictory records, evidence mismatch, or violated scope/preservation rules. |

The helper cannot authenticate a model's claimed command execution, infer omitted
requirements from prose, judge visual similarity, or prove semantic correctness.
It detects recorded coverage and byte-level inconsistencies. Real tool traces,
behavioral evaluation and later independent review remain necessary evidence.
Completion here is not an independent review, Visual QA pass, or release approval.

On resume, preserve earlier snapshots/results. Compare current inputs and source;
after input/HEAD changes capture a fresh baseline and reconcile affected requirements.
Treat new user edits as protected work, not drift to reset away. Verify incoming
review findings at their recorded target before changing code; do not inherit a
reviewer's request to expand scope or publish. Hand downstream reviewers the current
diff/target, input identities, requirement map, app setup and actual evidence.
