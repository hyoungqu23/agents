# Evidence and result records

Keep artifacts outside the source in one run folder: run.json, target-before.json,
target-after.json, report.md, assessment.json and evidence/. Preserve earlier attempts.
Start with this compact run shape; replace examples with actual values:

```json
{
  "schema_version": 1,
  "target": {"url":"actual URL","environment":"test","role":"actual role","backend":"actual API or not_applicable","served_build":"actual observed build or unknown","local_root":"optional absolute source root"},
  "journeys": [{"id":"J-1","goal":"Actual requested outcome"}],
  "checks": [{"id":"C-1","journey":"J-1","required":true,"axis":"visual","purpose":"Relevant screen visibility","expectation":{"source":"actual request/AC/design anchor","text":"Actual expected outcome","certainty":"confirmed"},"status":"blocked","reason":"Not executed yet","detail":"Pending actual observation"}],
  "issues": [],
  "data_operations": []
}
```

Omit local_root for remote-only work. `desired_revision` is optional in target; when
set, record the actual `served_revision` independently of the opaque deployment
`served_build` ID. Missing/unknown served_revision is a gap; a known mismatch is
invalid. Resolve requested branch/tag/PR references to the exact intended commit
before capture. For a cumulative set of PRs, identify the intended combined target
and retain how those PRs map to it instead of claiming one PR's exact head was served.
Optional `commit:` prefixes and full Git hash casing are normalized for comparison.
Target claims are externally observed;
this helper cannot authenticate a URL, role or served bundle. Record tool/version,
session identities, capabilities and charter in additional fields/report as needed.
Do not add secrets. Preserve initial check/journey definitions; exploration may add
checks but cannot weaken or erase existing ones.

```text
python3 /installed/dogfood/scripts/dogfood_result.py capture --run /state/run.json --output /state/target-before.json
python3 /installed/dogfood/scripts/dogfood_result.py capture --run /state/run.json --output /state/target-after.json
python3 /installed/dogfood/scripts/dogfood_result.py assess --run /state/run.json --before /state/target-before.json --after /state/target-after.json --output /state/assessment.json
```

Capture before and after execution. Capture hashes plan and source, not mutable
observation fields, so unchanged checks can target its digest throughout the run.
If exploration adds definitions, recapture and rerun affected checks; never reassign
old observations to the new digest. For changed source/target begin a new attempt,
retain old records and revalidate affected assumptions. The helper does not execute
commands, apps, URLs, browser input, install, authenticate or write external systems.
Its only writes are explicitly requested new output files.

Checks use passed/failed/blocked/skipped plus concrete detail; blocked/skipped need
reason and required ones remain gaps. Completed observations need `target` equal
to the after digest and nonempty `evidence: [{path, sha256}]` relative to the run
folder. Evidence cannot traverse symlinks or escape the folder. Preserve actual
tool output/trace, captures and only necessary logs. `target_evidence: {target,
evidence}` at run level records actual URL/role/environment/build observations.
Missing target evidence leaves a gap even if check records look complete.

For visual completed checks add `visual`: `image` (PNG/JPEG evidence path), `inspected:
true`, `inspection_trace` (actual image delivery/reading tool trace path in evidence),
`observation`, `pixels: [width,height]`, `css_viewport: [width,height]`, positive
`dpr`, `scale`, `capture: viewport/full_page/region`, `comparison_scope` (actual area,
reference version/method/masks/limits). The helper reads PNG/JPEG dimensions only; a
matching header/inspection record cannot prove correct visual judgment or full
image decoding. Use the host viewer to open the real image. Other image formats
need an actual disclosed conversion or a blocked metadata check, never a fake image extension.

For persistence add `persistence: {mode: real_api, requery_trace: evidence-path}`.
Retain actual observed requery/backend/UI evidence. Merely choosing real_api in JSON
is not proof of communication. Real Service Workers and fake-response mocking are
different. No internal state injection or response replacement by default.

Issues need stable `id`, `check`, current `target`, `expected`, `actual`, `steps`
(including data/preconditions), `impact`, positive integer `attempts`, `evidence`
and `classification: reproduced/observed_once/intermittent/unverified/needs_intent`.
A failed check requires an observed issue. Conversely, an observed failure issue
must reference a failed check; a passed/blocked/skipped check cannot simultaneously
claim that same confirmed failure. Give a different outcome its own check ID.
Keep hypotheses and uncertain intent
separate from observed confirmed-expectation failures. An observation need not
reproduce twice to be reported accurately.

Data operations need stable `id`, exact `created_ids` array, concrete `detail`,
`outcome: confirmed/unknown/failed`, `cleanup: done/not_needed/pending/failed`.
Done cleanup needs actual evidence. Unknown delivery and pending/failed cleanup
remain gaps. Requery before retries and clean only exact own-created IDs.

Assessment is complete when required scope/evidence/target/data work is recorded
consistently, partial with gaps, blocked when no required check could run, invalid
for stale/contradictory records or broken evidence. Product result is independently
issues_found/no_issues_observed/undetermined. Complete may include product defects.
Exit 0 = capture/complete; 2 = partial/blocked/invalid; 1 = tool/input/output error.
The recorder fingerprints local regular file bytes/modes and symlink identities;
.git/node_modules/.next/dist/__pycache__ are excluded runtime directories. Remote
state and generated bundles need separate observation, not claims from this hash.
