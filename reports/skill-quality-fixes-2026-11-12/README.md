# Skill quality corrections — 2026-11-12

Base: `1d5a9fb903e325cd80a7c4cbae7a69899081db66`. Runtime source hashes and forward-run identities are in [source-manifest.json](source-manifest.json). Four requested corrections are grouped into four commits. The original checkout's conflicts and untracked work were preserved.

## Changes and focused verification

| Correction | Result and evidence |
| --- | --- |
| dogfood exploration | Adding a check previously made unchanged observations invalid. The focused regression failed before the fix and passes after it. New per-check targets bind source, expectation and journey; 36 recorder tests cover repeated additions, preserved issues, stale expectations, borrowed targets and legacy captures. |
| study-loop hints | Learner-authored fields are distinguished from tutor hint text. A fresh-context actor used the real engine, saved one cue with the original learner request separately and retained answer waiting. Inspect [the journal record](study-loop/hint-record.json) and [actor response](study-loop/response.md). |
| review-respond progress | A fresh-context actor used an explicitly selected offline collection, fixed empty success handling, added a regression and committed locally while deferring the v2/performance request. The existing endpoint was preserved. Inspect [the outcome](review-respond/response.md), [actual source](review-respond/invoices.mjs), [regression](review-respond/invoices.test.mjs) and [parent verification](review-respond/verification.log). |
| SPEC reader parity | The standalone product and build copies remain independent at runtime. A source parity check and shared valid/invalid corpus reject duplicate/malformed AC rows, unsupported versions, fenced examples, invalid encoding and invalid question flags/impacts. |

## Repository checks

- `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`: 411 tests, 410 passed, one skipped because optional local design notes are not checked out. [Full output](unit-tests.log).
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/review-harness/src python3 -m unittest discover -s tools/review-harness/tests`: 29 passed.
- `node --test plugins/design/evals/tests/fixtures.test.mjs plugins/build/skills/implement/evals/files/feature-app/tests/*.test.mjs plugins/build/skills/fix/evals/files/project-list/tests/*.test.mjs`: 5 passed; loopback-server access allowed for the fixture.
- `./scripts/validate.sh`: passed with the official validator at CI-pinned `5c5308fc9a9ee789049d646ef11e5400384b9c6f`, PyYAML 6.0.2 in an external uv cache, and the installed Claude CLI. [Output](plugin-validation.log). Existing nonblocking directory diagnostics concern missing licenses/icons and install-line advice; version mismatches were corrected. No licensing or directory publication decision was made.
- `./scripts/load-check.sh`: all six plugins installed and enabled in scratch configuration, including all their skills.
- `skill-creator/scripts/quick_validate.py`: dogfood, study-loop, review-respond, spec and implement passed.
- 78 runtime Markdown files: no broken relative links. Six marketplace inventories and Claude/Codex plugin versions agree. `git diff --check` passed.

## Behavioral scope and limits

Two fresh collaboration contexts received raw synthetic inputs and candidate skills without evals. They did not receive the evaluator's expected answer, suspected defect or earlier conclusions. Exact model identity was not exposed; the actors inherited the session model. These are two bounded forward-use checks, not a quality score, cross-model benchmark, full behavioral suite, live GitHub integration test or browser QA of a product.

The actor responses and real output files are preserved. Raw tool-stream authentication is not available, and independent contexts do not establish independent model families. The parent checked the journal, current fixture source and native test results. Synthetic acme commit links in the offline response are drafts and do not point to published commits. No network collection, external reply, push or thread mutation was part of either forward run.

A parent-side Node verification first used the main checkout as its working directory and could not find the fixture test. The corrected command ran in the fixture checkout and passed both tests; the retained verification log is from that correct target. No failed execution was counted as a pass.
