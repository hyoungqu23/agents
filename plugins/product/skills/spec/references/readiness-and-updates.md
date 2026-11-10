# Readiness and updates

The handoff v1 canonical tables are SPEC §6.1 and QUESTIONS §1. Use one plain stable
ID per row; literal pipes are encoded as `&#124;`. Keep the bundled header spellings
and single-line scalar frontmatter. These limited conventions permit an independent
consumer to extract the full inventory without relying on a model's manifest.
Every canonical table row needs leading/trailing pipes; malformed rows are errors,
never absent ACs/questions. Handoff identity is read from actual frontmatter only.
Do not silently convert a preexisting document to this format during inspect-only
work. Explain unsupported formats and preserve the source for a deliberate migration.

The QUESTIONS frontmatter points back to the same SPEC and shares its feature
identity. Its status/blocking columns are canonical. Details explain original OD
relations, evidence/conflicts, implementation impact, blocking reason, resolution
condition, actual answer/authority (known or unknown), reflected SPEC location and
resolution/reopen history. Do not repeat current status in contradictory prose.
Closing a refuted concern requires its refutation evidence. Reopening keeps earlier
answers; a different question receives a new ID.

Four required reviews serve different purposes:

- Structure: canonical IDs are unique, references resolve, applicable sections and
  question impacts are present. A green helper checks only limited record structure.
- Source accuracy: trace material claims/decisions back to originals and versions;
  check partial/unavailable inputs and reverse coverage beyond ACs.
- Consistency: trace screen, rule, permission, API and AC together; detect opposite
  interpretations and unsupported state transitions rather than count references.
- Reconstruction: for every AC derive actor, initial state, action, request, success/
  failure UI result and newly needed assumptions from the spec and its named sources.
  Question consequential assumptions after checking all relevant source sections.

A separate reader may receive SPEC and named references without prior discussion;
a second source-reading review still matters. If only self-review is available,
record that limitation. Reader agreement is `not_detected`, not proof. Store review
scope/manner and limitations in SPEC §6.2; do not report inspections never performed.

Ready applies to the explicitly declared scope: required reviews performed and no
active blockers. Deferred+yes remains blocked; resolved+yes is historical; open+no
can remain ready with an explanation why it does not change the behavior contract.
Missing required review stays draft. Drafting useful independent work does not
resolve blockers. If a subset is requested, cite the authorized exclusion and retain
the original rest and affected questions instead of silently shrinking coverage.

On continuation reread actual contents, including user edits. Compare previous/current
SPEC, QUESTIONS and relevant source bytes or revisions; inspect affected links when
API/design/decisions change. A timestamp or unchanged document revision cannot prove
freshness. Patch affected sections only, increment content revisions and preserve
stable IDs. Removing an AC, exception or failure case requires supersession/exclusion
evidence. Record what changed and which reviews were actually repeated.

The implement handoff uses these same original tables. Its bundled consumer must
freeze both originals, map every AC (including justified exclusions), preserve
active Q → needs_decision and compare final code/behavior with original conditions,
expectations and API/UI rules. Neither spec ready nor its structural helper grants
permission to implement, certify runtime behavior or release a product.
