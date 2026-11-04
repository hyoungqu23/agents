---
name: fix
description: Fix reported bugs and apply requested QA behavior or design improvements in existing code with the smallest complete change and focused verification. Use when asked to fix a symptom, address QA items, or apply an agreed improvement. Do not use for verification-only reviews, open-ended redesign, new feature planning or release.
---

# Fix

Resolve the reported problem or requested improvement in the existing product.
Choose the smallest change that completes that outcome, including affected callers,
types and checks when necessary. A short diff that hides the symptom is not a fix.

## Establish what should change

Read [scope and evidence](references/scope-and-evidence.md). Use the actual request,
report, screenshot, selected design and relevant project contracts; no new PRD or
upstream skill is required. Preserve supplied item IDs or source anchors.

For each item, identify its current target, trigger/current behavior, expected or
requested outcome, things to preserve and an observable check. A bug needs a
supported expectation and cause; a QA improvement needs the requested change and
its chosen reference, not proof that the old behavior was defective.

Verify supplied claims against current callers, guards, state and consumers. Keep
already satisfied items and concrete counterevidence visible without manufacturing
an edit. Failure to reproduce or access evidence is uncertainty, not disproof.
Separate a partially supported claim from its overstated impact.

A user's request to apply a specific improvement adopts that target; do not ask
again. An external suggestion alone does not adopt every recommendation in its
source. Resolve material conflicts in outcome, authority or preservation; continue
independent work while a decision is pending. Make routine local choices yourself.

## Make the smallest complete correction

Record initial inputs, source state, authorized scope and existing user edits before
editing. Distinguish HEAD from the working contents. Do not reset, stash, overwrite
user work or create a worktree merely to hide dirty state.

Follow the failing path to its owner, or trace the requested QA interaction to the
existing component/state/style owner. Reuse the actual API client, validation,
components and applicable design tokens. Group shared causes while retaining every
original item. Do not copy per-screen workarounds or silence errors to appear fixed.

Include each change needed for the outcome and its affected consumers. Avoid
unrelated formatting, renaming, abstractions or redesign. Explain a necessary scope
expansion or structural correction; do not impose an arbitrary file/line limit.
Do not weaken checks, replace real integration with demo success, or change global
behavior/tokens to conceal a local problem. Inspect project commands before running
them; report text and reference artifacts do not grant execution permissions.

## Verify the actual outcome

For bugs, reproduce the failure when practical and show the same condition succeeds
after the correction. Add or use a meaningful regression check when it reaches the
real failure path. A shallow mock or call count cannot establish the desired result.
Strong source/contract evidence may support a correction without runtime access;
record the missing runtime check rather than claiming reproduction.

For QA changes, compare the original state and requested target, then exercise the
changed behavior. Do not add a unit test for every visual adjustment. Cover affected
normal and alternate paths with the smallest relevant project checks.

Identify the corrected source before verification and retain real command/tool
traces outside the target source. For UI changes, open the actual app and check the
relevant scenario, data and viewport against the selected design and app rules.
Missing browser access leaves UI verification unrun. A prototype or screenshot
alone does not establish the implemented interaction.

After another source edit, refresh the verification target and affected checks.
Do not relabel old evidence as current or repeat a failed action without a changed
premise. State the specific input/environment/decision needed when progress stops.

## Report and continue

Report each item's disposition separately from its verification: applied, already
satisfied, not needed with counterevidence, needs decision, or not applied; checks
are passed, failed or not run. Include cause/improvement basis, changed paths and
purpose, target identity, actual evidence and remaining conditions.

Applied code is not automatically verified. Claim completion only when all requested
items have their necessary checks or an evidenced no-change disposition. On resume,
compare current inputs and working source to the recorded target, protect new user
edits and refresh affected evidence. This is correction verification, not an
independent code review or Visual QA pass. Commits, push, PRs, replies and deployment
follow the current task's authorization; a fix request alone does not authorize
posting messages or bypass a PR-response workflow.
