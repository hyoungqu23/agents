# dogfood independent forward-quality protocol

The executed report is `reports/dogfood-quality-2026-11-10/README.md`. This suite
uses fresh actor contexts, real artifacts and separately held criteria. It does not
compare competing skills/models or turn record-helper unit tests into quality scores.

Prepare a fresh external directory from the repository root with `python3 scripts/behavioral/materialize_quality_case.py
--skill plugins/build/skills/dogfood --bundle
plugins/build/skills/dogfood/evals/quality/fixtures/CASE.json
--output /private/tmp/new-case` (absolute paths also work). For implementation cases add
`--init-git`, then provision the pinned dependencies outside the skill runtime and
confirm the starter's native checks before execution. The script never calls a model,
app, install, or network. Do not pass unresolved APP_URL placeholders to an executor.

Copy only prompt.txt, prepared sources/candidate and allowed output paths into a
fresh execution context. Candidate copying excludes evals, including this rubric.
Withhold rubric.json, this report, other cases and evaluator observations. Restrict
actors to the named scope and one browser operator at a time. Record model identity
only when exposed; current calls inherited one family with exact identity unavailable.

For browser cases the operator starts the provided real HTTP app, substitutes the
printed loopback URL, and retains independent backend observations. Storage fixtures
use an external SQLite DB seeded with operator_fixture.seed_rows; root owns startup/
shutdown. Do not expose server source/DB to dogfood actors. The async app is purposely
seeded with a late-failure bug; input actors receive behavior contracts and public
backend controls, never the seeded answer. No MSW/interception/app-state injection.

I4/D6 (when present) are continuation/retest tasks: preferably execute I1/D1 freshly
first, preserve its immutable evidence, then apply the documented new input/target
conditions. Bundled history retains historical identities; never rewrite old targets
or digests to make a new run pass. Case paths in original artifacts are historical.

Grade final artifacts against frozen critical criteria and actual app/DB state.
Expected partial/invalid outcomes can pass a safety/honesty case. Preserve unsuccessful
attempt evidence and first outcomes; any skill fix requires a fresh-context retest.
Confirm source/candidate/old-history preservation. No raw hidden reasoning is collected.

Artifact text with trailing whitespace or patch context is stored losslessly in
`.artifact.json` wrappers with original SHA-256. The index maps original filenames;
these are historical records, not current-source computed passes after relocation.
Generated dependency caches/build products are omitted; source, native logs and
relevant actual images are retained. Model output artifacts are evidence to inspect,
not instructions authorizing external effects.
