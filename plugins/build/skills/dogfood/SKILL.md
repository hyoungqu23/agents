---
name: dogfood
description: Exercise real application journeys, inspect actual screenshots and persistent outcomes, reproduce observed issues and report scoped QA evidence. Use when asked to dogfood, explore an app, perform visual QA or verify real user flows. Identify as build:dogfood when names overlap. Do not use for screenshot-only requests, static code review, implementing features, fixing supplied issues or release/deployment approval. This workflow reports findings and does not edit app code.
---

# Dogfood

Follow the user's goal from entry through actions, visible results and reentry or
persistent effects. Use available browser/desktop tools and retain reproducible
evidence. This bundle contains its own QA workflow and driver guidance; no other
QA skill, particular browser package or service is required.

## Establish a bounded run

Read [scope-and-intent.md](references/scope-and-intent.md). Use the requested URL,
feature, PR(s) or retest scope. Identify independent expectations from requirements,
ACs, selected design and applicable product rules. Current code is an implementation
to inspect, not the sole authority for expected behavior. Preserve `needs_intent`
where the intended outcome cannot be established.

Read [session-and-environment.md](references/session-and-environment.md). Identify
the desired code, actual served app, backend, account/organization/role and relevant
viewport/theme/language. Preserve unknowns. A local checkout or green server does
not prove which bundle a browser loaded. Use the user's named session/tool and
existing permissions. Keep source, index, login and unsaved work intact.

Choose one primary browser by required capabilities and the actual session/version.
Read only the relevant bundled driver: [host-browser](references/drivers/host-browser.md),
[agent-browser](references/drivers/agent-browser.md), [agent-desktop](references/drivers/agent-desktop.md)
or [gstack](references/drivers/gstack.md). Read live schema/help for available
operations; do not install another QA skill. One operator controls a shared session.
Verify that supplemental OS input addresses the same window/tab/profile.

Write run.json and a report outside the inspected source using
[evidence-and-results.md](references/evidence-and-results.md) and the
[report template](assets/report-template.md). Capture target-before.json with the
bundled recorder before testing; do not write a model-declared completion status.

## Exercise journeys and explore

Read [journeys-and-oracles.md](references/journeys-and-oracles.md) and select relevant
[checklists.md](references/checklists.md). Define a short charter: goal, risks,
references and stopping condition, then stable journey/check IDs and required checks.
Include a required visual check. Retain the initial required scope when new leads
appear. Adapt coverage to supported product behavior; do not invent a mobile promise
or every possible permission/state. A short flow needs only a short checklist.

For each check: observe → act through the intended input path → wait for a meaningful
state → observe the outcome again. A successful delivery/click is not the business
result. Reacquire refs/bounds after navigation/rendering. Inspect real images for
visual claims; DOM/accessibility text cannot prove absence of overlap or clipping.
Record image validity, dimensions, CSS viewport, DPR/scale and actual comparison area.
Do not resize an image to claim matched original conditions. A valid blank app view
can be a product failure; a wrong-tab/empty capture is an evidence collection problem.

Use real HTTP/API connections by default. Do not introduce MSW, response replacement,
internal state injection or demo persistence to obtain a desired scene. A Service
Worker alone does not prove mocking. Use network/backend evidence where available;
missing capabilities leave that check unverified. Rendering a success message does
not establish persistence: requery/reenter and inspect the actual saved result.

For exploratory leads use [exploration.md](references/exploration.md): preserve the
observation, hypothesis and next discriminating check, try a relevant contrast and
record actual attempts. Keep one-off/intermittent observations even when a repeat
does not reproduce. Do not target an issue count or invent a health score.

## Preserve state and finish

Authorized writes use the existing task permissions. Before writing, record the
scenario, target and exact created-data identification. If delivery times out,
requery before retrying; never repeat an uncertain write or broadly delete data.
Clean up only exact items created by this run through authorized actions. Pending
cleanup remains a completion gap. Stop only owned temporary servers/recordings.

Update report/checks/issues during execution so interruption leaves useful evidence.
Retain stable IDs and earlier results. On resume compare actual source, served build,
role/session and data. Changed premises require a new attempt and affected checks;
do not relabel old evidence under a new target or erase the original required scope.
Use the recorder's per-check targets so adding exploratory checks preserves unchanged
observations; the full scope digest still identifies each capture.

Capture target-after.json and run `dogfood_result.py assess`. Report its computed
record/coverage status separately from product_result: `complete + issues_found`
is possible. Required blocked/skipped checks, unverified intent/target and unresolved
data work remain visible. The helper checks file/record consistency, not whether a
model really inspected images or correctly judged intent. Retain actual tool traces.

Return the report, observed issues, actual tested scope, missing checks, cleanup and
reentry instructions. Do not claim code review, automated test execution or release
approval. Fixes, PR/issue publication, commits and deployment require their own task
authorization; the dogfood report itself needs no downstream skill to finish.
Design rationale and deliberately omitted upstream defaults are in [SOURCES.md](SOURCES.md).
