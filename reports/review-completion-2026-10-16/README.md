# Structured review completion evaluation

This change separates recorded review completeness from Pending persistence.
`review-result.json` is checked against current Git identity, the full changed-file
inventory and source quotations. A stale result is invalid; missing/deferred work
is partial. Pending comments must match eligible finding IDs, anchors and text.
The checker does not certify reasoning or whether a claimed command actually ran.

## Model results

| Scenario | Codex gpt-6-astra | Claude claude-sonnet-5-5 |
| --- | --- | --- |
| Known permission predicate defect, with a guarded non-defect nearby | Passed: one supported permission finding, no guard false positive | Passed: one supported permission finding, no guard false positive |
| Equivalent refactor, corrected clean fixture | Passed: no supported findings | Passed: no supported findings |
| Only permissions.py reviewed; two other changed files explicitly deferred | Passed: supported finding with computed partial scope | Passed: supported finding with computed partial scope |

These are six selected outcomes from eight real model executions. The source and
plugin hashes remained unchanged in every run. The parent recomputed assessments
from source; model-written success flags were not authoritative. Evaluations ran
against local synthetic Git repositories and made no GitHub writes.

### Initial clean-fixture error

The original clean fixture replaced tuple membership with set membership. That was
not equivalent for every input allowed by the supplied contract: a list/dict role
returned False before but raises TypeError with the set. Both models raised this
valid issue, so the original grader marked both clean runs failed.

The original results and reports remain under `codex-clean` and `claude-clean` and
are identified as invalid clean fixtures in `runs.json`; they are not counted as
model false positives. The corrected fixture adds only parentheses to the same tuple
membership expression. A regression test compares both versions for permitted,
unknown, None and unhashable inputs. Only the clean case was rerun on each host.

### Qualitative inspection

Both hosts found the actual `or` predicate defect and rejected the empty-list
accusation because the early-return guard still handles it. The corrected clean
reports excluded cosmetic parentheses and verbosity objections without a finding
quota. Partial reports retained `lookup.py` and `notes.md` as unreviewed and explicitly
said the review was incomplete.

Both initial defect runs first omitted the required copy-ready `comment` field.
The checker returned partial rather than accepting them; the agents preserved that
initial assessment, completed the result and revalidated. They did not modify source
to make the check pass. Raw intermediate artifacts are retained in the local runs.

Severity and prose are still model judgments: Codex used P2 for the predicate
contract violation and Claude used P1, with external-callsite uncertainty disclosed.
One Claude clean report misstated the total repository file count, while its actual
three-file changed inventory was correct. These cases validate the specified bounded
outcomes, not every sentence or every review criterion.

## Deterministic and independent checks

- Real Git tests cover complete/partial/invalid results, stale SHAs/diffs, missing,
  duplicate and unreviewed coverage, bad quotations, unsupported candidates and
  verified findings surviving unrelated scope gaps.
- Working-tree tests include staged/unstaged changes that cancel, untracked files,
  binary/index changes, executable bits, symlink types and path-boundary behavior.
- Gitlink changes remain visible even with local ignore settings. Both the Pending
  and review-result tools reject dirty submodule checkouts consistently.
- Pending tests reject missing/stale results and unresolved or mismatched comments,
  and preserve partial status independently of successful Pending persistence.
- Grader sensitivity tests reject a missed defect, a mechanically valid false
  accusation, and a full-coverage claim for explicitly deferred files.

Independent review reproduced two fingerprint/inventory defects: untracked file
type/mode changes and Git settings hiding gitlinks. Both were fixed, regression-tested
and independently revalidated. No new Pending-only integration issue remained.

Local validation passed all 130 Python tests, including the final boundary and
fixture checks. CI repeats the full suite on the PR. Node tests passed 3/3. Official Codex/Claude plugin
validators and all plugin load checks passed.

## Evidence and reproduction

`runs.json` keeps original execution records, exact prompts, source files and before/
after hashes, selection rationale and local raw-evidence paths. Each case directory
contains the model result, host assessment, human report and compact tool-call trace.
Instruction manifests identify the exact plugin files used. Full stream events and
intermediate attempts remain under the recorded `/private/tmp` paths; compact traces
omit tool outputs and provider initialization metadata.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'
# Requires authorization for synthetic model-service calls:
python3 scripts/behavioral/review_completion.py --host codex --model gpt-6-astra --output /tmp/completion-codex-new
python3 scripts/behavioral/review_completion.py --host claude --model claude-sonnet-5-5 --output /tmp/completion-claude-new
```

Current runner outputs use the corrected clean fixture. `final-source-hashes.json`
records the implemented files. Provider model aliases and this local host are not
immutable environment snapshots. No before/after detection improvement, live GitHub
write compatibility, general false-positive rate or exhaustive quality is claimed.
All authorized PR comments continue to remain Pending; no submit path was introduced.
