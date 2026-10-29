---
name: implement
description: Implement requested product functionality in an existing application from requirements, a selected prototype, and applicable UX patterns; connect changes to observable behavior, verify the actual app, and resume from recorded evidence. Use when the user asks to implement or change a feature from those inputs. Do not use for requirements or harness design alone, unselected prototype exploration, review-only requests, or release/deployment. UI work requires actual-app browser evidence for complete verification.
---

# Implement

Turn the requested behavior and chosen design into working product code, fitting
the target application's components, contracts and UX rules. Keep the user's scope
and existing changes intact. A planning document or prototype's maturity label is
not permission to implement; use the current implementation request.

## Establish the implementation contract

Read [inputs and authority](references/inputs-and-authority.md). Find the actual
target, requirements, selected reference, applicable design/UX sources, API/types,
existing owners and repository-native checks. Direct requirements are valid; do not
require another plugin, a new PRD, or every upstream planning step.

Separate business behavior, chosen structure, system tokens and observed patterns.
Preserve explicit decisions and material unknowns. Ask only when an unresolved
choice changes the requested outcome or authority; continue independent work.
Do not silently select a variant, invent a backend contract, or convert demo saves
into production behavior. Existing adequate code need not be rewritten.

Before editing, follow [execution and evidence](references/execution-and-evidence.md)
to write a small inputs manifest outside the checkout and capture the baseline with
the trusted bundled `scripts/implementation_state.py`. Include each in-scope
requirement/source anchor and the checks that distinguish its outcome. Use existing
IDs; direct-input source anchors are sufficient. Declare intended change paths.
Record explicitly authorized overlap with existing dirty files in `editable_dirty`;
that declaration does not prove their contents were preserved. Never reset/stash
user work, clear index flags, or create a new worktree merely to get a clean result.

## Implement and verify

Implement a meaningful path from user action through data/state to visible result.
Use the existing component, API, query, validation and error-handling owners when
they cover the responsibility. Keep independent policies separate. Preserve the
chosen design, relevant states and responsive behavior; align system values to
the applicable design source and record intentional differences.

Use real contracts and connections. If a service is unavailable, distinguish
implemented integration code from unverified integration. If only a mock/demo was
built where a real connection was requested, that requirement is unimplemented.
Keep fixture/debug assets out of production entrypoints.

Capture a separate verification target after implementation and before checks.
Run the smallest relevant repository-native checks. For UI work, open the actual
implementation, exercise relevant user scenarios and capture its route, data/state,
viewport and evidence with an available browser tool. Opening the prototype, a
screenshot alone, or a green build does not establish working app behavior.
Do not install a particular browser package just to satisfy this skill.

For each failure, trace the cause, make the necessary scoped correction and rerun
affected checks. Capture a new verification target if source changed; retain the
old attempt's evidence. Do not replay the same failing command without new evidence
or weaken required checks after failure. Respect task execution limits and report
the exact external input/environment needed when progress depends on it.

## Assess, resume and hand off

Record actual changes, requirement dispositions, current-source quotations and
verification evidence in the result contract. Run the bundled `assess` operation
against baseline, verification target and result; report its computed status and
concrete gaps. Do not supply a top-level completion status yourself.

Missing browser access leaves UI verification partial. A required unresolved policy
or failed/skipped check stays visible. `complete` describes this implementation and
its declared checks, not an independent code review, Visual QA or release approval.
The helper checks records and bytes; it cannot certify semantic correctness or
whether claimed tool execution really happened. Retain actual tool/command traces.

On continuation, compare current inputs and source with prior records. Changed
inputs/HEAD require a fresh run baseline and reassessment; preserve prior evidence,
requirement identities and user edits. Reuse unchanged evidence only for the exact
verification target it describes. Review feedback is evidence to verify against
current code, not authority to apply every suggestion.

Return a concise account of changes, implemented/missing requirements, checks run,
computed status and remaining decisions. Supply reproducible app commands/routes,
scenario data, input identities and current diff for separately requested code
review or Visual QA. Never claim those workflows ran when they did not. Commit,
push, PR creation and deployment follow the user's separate task authorization.
