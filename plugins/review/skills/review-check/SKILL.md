---
name: review-check
description: Check whether existing review comments from a person, model, or bot are correct against the target code and requirements, without changing code or posting replies. Use when asked to verify a pasted review, challenge a finding, check a suspected false positive, or recheck an older review. Do not use to discover new issues; use review-code, or review-pr for a fresh PR review. Use review-respond to fix and answer reviews on your own PR.
---

# Review Check

Check a review's claims and explain which ones hold, which do not, and what remains
unknown. The Korean label is **리뷰 지적 검증**. A PR is optional: pasted text, a
review file, and a supplied code snapshot are valid inputs.

## Scope and inputs

Use the supplied claims, target repository or snapshot, and requested revision.
If the user gives no revision, use the current checkout and record HEAD plus
relevant working-tree changes. With snapshot-only input, say so; do not invent a
commit SHA. Record the original review revision separately as unknown if absent.

If the claims themselves or the target cannot be identified, ask for that missing
input. A missing fact about one claim does not block checking independent claims.
PR ownership is irrelevant for this read-only skill. Read PR content when needed,
but do not create a worktree, switch branches, or invoke a posting workflow simply
because the input includes a PR URL.

Default to read-only investigation and an answer in the conversation. Do not edit
source, stage, commit, push, post comments, resolve threads, or change review state.
Save reports only when requested. If the user also explicitly asks for fixes,
finish the verification first, then hand the supported actions to the appropriate
implementation workflow within that authorization; do not add a redundant approval
step. The read-only check itself never grants mutation permission.

## Check the claims

Apply [claim-verification.md](../../references/claim-verification.md). This is the
same evidence procedure used by review-respond; no other skill needs to be installed.

1. Inventory the supplied claims. Retain their IDs or assign stable `RC-001` IDs.
   Keep original wording and reviewer priority as attributed input. Split mixed
   claims for analysis, but retain one aggregate record per original ID: a mixed
   supported/refuted claim is partial. Put the subclaim reasoning in its evidence
   and counterevidence. Preserve aliases when duplicates are grouped.
2. For each claim, trace the target code and requirement, try counterevidence, and
   record checks actually executed. Use primary contract sources when available.
   Do not broaden this into a whole-repository audit or chase unrelated defects.
3. Assign `confirmed` (타당), `partial` (일부 타당), `refuted` (오탐), or
   `unresolved` (미확인). Track current state separately so a fixed historical bug
   is not labeled an original false positive. Explain the supported portion of
   every partial verdict.
4. Reconcile the inventory: every input ID must have a verdict or an explicit
   duplicate mapping. A missing source stays unresolved. Do not force a positive
   or negative finding, assign severity to uncertainty, or omit inaccessible items.
5. Summarize supported changes in one proposed action list, dependencies first.
   Keep unresolved questions separate; recommendations are not executed fixes.

If a prior report is supplied, preserve claim IDs and recheck evidence affected by
changed code or requirements. Do not overwrite or create a report without a request.
Carry forward a result only when its cited evidence remains current, and label it
as carried forward rather than a newly executed check.

## Output

Use the user's language. Lead with the disposition of the supplied review, then
provide one concise record per claim with:

- ID, original claim, and original review revision if known;
- target revision and current state;
- verdict, evidence locations (`file:line` or snapshot section), trigger and impact;
- counterevidence, missing evidence, and recommended action as applicable.

For `already_addressed`, distinguish the original condition from the current fix.
For `unresolved`, state the question or artifact needed to settle it; leave verified
severity unset. Finish with claim coverage, checks run and their results, checks
not run, and limitations. Never call this a complete code audit.

When the user requests a saved report, save a human-readable report and a JSON
companion alongside it, using the requested format/path as the base. If only JSON
is requested, return only JSON. Each JSON claim has these keys:

```json
{
  "id": "RC-001",
  "aliases": [],
  "claim": "The supplied assertion",
  "review_ref": null,
  "target_ref": "snapshot: input.md",
  "verdict": "unresolved",
  "current_state": "unknown",
  "evidence": [],
  "trigger": null,
  "impact": null,
  "counterevidence": [],
  "missing_evidence": "The server contract is unavailable",
  "action": "Obtain the matching server contract",
  "verified_severity": null
}
```

The enclosing report has `claims`, `coverage` (`input_ids`, `handled_ids`,
`limitations`), and `checks` (each with `command`, `result`, and `executed`). Use
null for genuinely unknown values, not invented refs or severity. Locations in
`evidence` and `counterevidence` must identify the inspected source. JSON validity
is a format check, not proof that the verdict is correct.
