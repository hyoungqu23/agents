# Original SPEC coverage — mandatory completion gate

The bundled `spec_handoff.py` supports the v1 Markdown contract without a product
plugin. `capture` reads the frozen SPEC §6.1 AC table and QUESTIONS §1 directly and
stores the extracted content in `coverage`; `assess` captures current bytes again.
A model-written pass flag or AC inventory is never the canonical input.
Frozen Markdown must be UTF-8 text; unreadable Markdown is a coverage gap. Binary
visual references remain supported. Automatic detection inspects only actual
frontmatter, so handoff examples inside a direct request do not activate this gate.

Supported frontmatter: single-line scalar `id`, positive `revision`,
`handoff_version: 1`, `status: draft/blocked/ready`, local `questions: ./QUESTIONS.md`.
QUESTIONS has a matching `questions:*` identity and local `spec` backlink.
The canonical table headers are:

```text
SPEC: AC ID | 근거 | 사전 조건 | 행동 | 기대 관찰 결과 | 관련 화면·흐름·API | 확인 방법·미결 참조
QUESTIONS: ID | 종류 | 질문 요약 | 영향 절·AC·범위 | 미해결 시 차단 | 상태
```

Use one row per stable ID, leading/trailing pipes, and `&#124;` for literal pipes.
Do not read tables in fenced examples as requirements. Nonempty ACs are required;
a header-only question table is valid. Question flags are `yes/no`; states are
`open/deferred/resolved`. An active blocker is yes + open/deferred. Enumerate all
affected canonical IDs (or `*` for every AC). Section-only/range impacts, malformed
rows (including a missing leading/trailing pipe), missing companions and unsupported versions are gaps, never empty successful
coverage. Direct requirements without a structured SPEC keep the existing contract;
that path does not claim original-document semantic completeness.

## Before edits

Inspect capture's `coverage` and compare every AC's condition/action/outcome,
UI/API contract and verification purpose with the execution requirement. Preserve
stable IDs and links. An active blocker must link each affected required result row
to `state: needs_decision` and `questions: ["Q-ID"]`. It remains a completion gap.
Resolved/nonblocking questions do not create blockers. SPEC blocked and implementation
partial/blocked have different meanings: independent work can proceed.

For a user-authorized partial delivery, retain every excluded AC with `disposition:
excluded`, a concrete `reason`, and `exclusion: {source, quote}`. The source must be
frozen with `role: scope_authority`; the exact quote must identify that AC and the
explicit exclusion. Read its actual authority; the helper validates the citation,
not who authorized it. An arbitrary reason, missing AC row or late scope reduction
cannot substitute. Excluded ACs and their questions remain in the extracted catalog.

## Before completion

Write one `source_review` entry per required canonical requirement in result.json:

```json
{
  "id": "AC-1",
  "target": "actual verification digest",
  "ac_digest": "digest of original extracted AC row",
  "facets": {
    "condition": {"expected": "original 사전 조건 cell", "verdict": "matched", "detail": "Actual manifest/code comparison"},
    "action": {"expected": "original 행동 cell", "verdict": "matched", "detail": "Actual comparison"},
    "outcome": {"expected": "original 기대 관찰 결과 cell", "verdict": "matched", "detail": "Actual comparison"},
    "interfaces": {"expected": "original 관련 화면·흐름·API cell", "verdict": "matched", "detail": "Actual API/UI trace, or applicable absence"},
    "verification": {"expected": "original 확인 방법·미결 참조 cell", "verdict": "matched", "detail": "Why the actual assertions distinguish the outcome"}
  },
  "behavior_checks": ["actual-required-command-or-browser-check-id"],
  "evidence": [{"path": "source-review.txt", "sha256": "actual evidence digest"}]
}
```

Use the helper's `digest(original_row)` function (SHA256 of sorted UTF-8 JSON with
its default separators and ensure_ascii=False). Store the actual source/manifest/
code comparison trace in evidence. `matched` must follow reading the original and
implementation, not simply comparing ID presence. Record mismatch/unreviewed and
its impact when no match is established. Evidence still targets the current full
verification digest. Required linked behavioral checks must pass; static ID scans,
a build that never asserts the requested behavior, and copied expected text do not
establish behavior. For noninteractive requirements choose a relevant executable
assertion instead of inventing a UI. For UI requirements exercise the actual app.

`assess` refuses complete for missing/ambiguous AC mapping, unsupported source,
missing review, changed inputs, any unmatched facet, unverified behavior or active
blocker. It can check records and source bytes; semantic judgments and real tool
execution require reading/code tracing and actual behavior evidence. Preserve that
limit in the report. Do not claim that this helper understands arbitrary prose.
