# Behavioral evaluation protocol

These scenarios are definitions, not execution results. Start with a scratch copy
of the skill, a realistic user request and the raw relevant fixtures. Give only the
request, skill and allowed app/data/documents to the executor; keep expected answers
and grading information outside that context. Do not install other QA/spec skills.

Observe actual source reads, output edits, tool traces and evidence; compare claims
with originals and actual app/server state. Preserve initial user work and source
hashes. Mechanical unit tests check record/format invariants separately and never
establish model quality. Record exact host/model when exposed, tools, limitations
and actual execution mode (self-run/separate call). Do not claim independent review
from self-authored outputs. No competitive benchmark or fixed issue quota.

Start with the local supplied fixture, then cover the listed conflicts, stale-input,
partial-scope and unavailable-capability cases. GUI/profile/native input and real
product environments need separate authorized runs; unexecuted combinations remain
untested. Keep run artifacts outside the inspected source and do not publish issues.

## Executed quality suite — 2026-11-10

6 independent-context forward tasks were executed with this skill version.
See [the quality protocol](quality/README.md), prepared input bundles and withheld
rubric. Existing mechanical tests are reported separately. The repository report is
`reports/dogfood-quality-2026-11-10/README.md`; it states what was and was not tested.
