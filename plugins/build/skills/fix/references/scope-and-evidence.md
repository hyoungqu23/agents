# Scope, targets and evidence

Keep the input's format and provenance. A short item table or task note is enough;
do not require a new parser schema, external plugin or completion engine.

## Choose the correction

| Question | Evidence to use |
| --- | --- |
| What was requested? | Current user request, supplied item IDs, explicit decisions and scope. |
| What should a bug do? | Applicable requirements, real contracts, consumers and supported product paths. |
| What should the QA improvement become? | The requested behavior and chosen design, including conditions and intentional exceptions. |
| Which system values apply? | Target app's design authority, components/tokens and explicit overrides. A prototype's demo color is not automatically an override. |
| Does the issue still exist? | Current source/state and reproduction; old review locations may have moved or been fixed. |

Missing permission policy, conflicting selected designs or incompatible API contracts
are material unknowns. A local code choice supported by the current app is usually
not. Do not adopt speculative preferences as defects or discard a QA improvement
simply because the old behavior was intentional. A requested improvement can change
intentional behavior; record that change and preserve the rest.

For a bug, trace trigger -> caller/state -> owning rule -> observable failure.
Check guards and alternate paths before accepting the proposed cause. For a QA
item, trace current interaction -> requested difference -> affected owners ->
observable target. Check related consumers when shared code changes. Prefer a
local correction using those owners; introduce structure only for a demonstrated
need in this task. Explain why a larger correction is necessary when it is.

## Keep source and verification distinct

Before editing, record the actual task inputs and inspected references, HEAD,
relevant staged/unstaged/untracked work and allowed paths. After correction, identify
the source being checked using the host's available revision/content/diff tools.
For an uncommitted target, HEAD alone is insufficient: retain the working diff and
contents/identities of relevant new files. Keep notes/evidence outside the edited
source unless the task specifically requests repository documentation.

Do not claim a computed digest or status unless a trusted tool actually produced
it. No bundled mechanical assessor is required by this skill. A snapshot can check
identity; it cannot prove the report's reasoning or that a command actually ran.
Do not invoke an unavailable sibling skill's helper through a guessed path.

Every reported pass describes a specific target and conditions. Record actual
command, working directory, exit/result and output, or actual app tool, route,
scenario/data, viewport and relevant captures. Note service/environment limits.
Observe the target after checks as well; generated source changes need a fresh
target and verification. Preserve earlier attempts instead of overwriting them.

Check the outcome, not merely the existence of new code. For a race, verify which
result is rendered after responses complete out of order. For a new reset action,
verify its actual state transition and the selection that must survive it.
Use a regression test when useful; a visual-only adjustment may need actual-app
comparison rather than another implementation-shaped assertion.

## Item results

Retain each original item, even when one change addresses duplicates. Separate:

- **Disposition:** applied, already satisfied, not needed with counterevidence,
  needs decision, not applied.
- **Verification:** passed, failed, not run, with the actual checks and evidence.

For no-change results, cite current evidence and distinguish already fixed from an
unsupported accusation. Unknown original source does not establish historical
validity. No reproduction is not counterevidence.

Failed/unrun necessary checks or unresolved targets prevent full completion. An
applied UI correction without a browser remains useful work with unverified UI.
Report the specific gap without implying an independent review or release pass.
