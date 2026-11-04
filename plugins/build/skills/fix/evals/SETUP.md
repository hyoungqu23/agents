# Fix forward evaluations

From this repository, use `python3 scripts/behavioral/fix.py prepare --case
bug|qa|no-change|no-browser --output NEW_EXTERNAL_DIRECTORY`. The preparer uses
the existing implement app's infrastructure plus this skill's complete-list overlay;
no package install, credential or external service is needed. This tooling is an
optional repository evaluation, not an installed fix dependency.

Give an independent executor only `prompt.txt` and its prepared source/skill/state
paths. Keep coordinator metadata, expected answers and grading code outside that
executor's authorized inputs. Record real host/model/tool limits. It must run the
task, not inspect the grader. Use fresh directories for retries.

The small evaluation-only result adapter asks for item dispositions, separate
verification states, changed-file hashes and actual evidence paths. It is not a
required runtime schema for fix. No generic assessor is installed with the skill.

After execution, inspect the code and actual traces. Independently replay the app
and run `node --test scripts/behavioral/fix-contract.test.mjs` with FIX_APP pointing
to the prepared source. This executes that synthetic app's model; inspect it first
and use the authorized isolated workspace. For the bug case, also run the executor's
new regression against the retained original model in a separate scratch copy.

Exercise latest-response success/failure, selection preservation, current-filter
Retry and empty success. For QA, observe the actual Clear filter action, select
synchronization, retained selection, hidden action in loading/error/nonempty states,
and the bordered empty group at wide/narrow sizes. Record actual observations and
the final source hashes outside the executor's inputs, then pass them to `grade`.
Parent browser observations never upgrade a no-browser executor's unverified result.

For coordinator Python tooling, import `fix` from `scripts/behavioral` and bind
observations to `gate.digest(source_hashes(snapshot))`, where `snapshot` is obtained
with `gate.capture(source, coordinator / 'inputs.json')` before observing the app.
Re-capture afterwards and verify it still equals that snapshot. Use this Git
inventory for source identity, not the generic instruction-directory hash helper:
nonignored `__pycache__` files are source entries, while ignored runtime files are
outside the captured source inventory. A separate scope guard still checks for
new ignored files outside the authorized paths. Initial dirty or untracked test drafts
are protected user work rather than test blobs assumed to exist in HEAD.

The grader checks identity, scope, protected inputs/user work, original test prefixes, changes, item
coverage, evidence files and independently supplied observations. It does not run
app code or authenticate a claimed command/browser execution. Coordinator metadata
and observations must be protected and actual traces inspected. Tests using synthetic
records exercise grader sensitivity only; they do not establish model behavior.
