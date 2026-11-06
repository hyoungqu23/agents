# Engine protocol

The complete contract is `scripts/studyloop/contracts.schema.json` (JSON Schema
2020-12). This page is the working summary. Every field shown is required;
unknown fields, `NaN`, `Infinity` and duplicate keys are refused.

## Envelope

```json
{
  "protocolVersion": 1,
  "workspaceId": "lowercase uuid, chosen once at init",
  "operationId": "fresh lowercase uuid per new write; reuse only to retry",
  "expectedRevision": 0,
  "actor": {"host": "claude-code", "hostVersion": null, "model": null, "authMode": "unknown"},
  "command": "workspace.init",
  "payload": {}
}
```

Find the `workspaceId` of an existing folder in `workspace.json`, or in the first
line of `records/events.jsonl` if `workspace.json` is missing.

Success: `{"ok": true, "revision": N, "committed": bool, "replayed": bool,
"viewsStatus": "current|stale|not_applicable", "result": {...}}`. A write returns
`result.kind = "transition"` with `entityIds` and the new `packet`. A replayed
write (same `operationId` and same request) returns the original IDs and does not
write again.

Failure: `{"ok": false, "committed": false|null, "error": {"code", "message",
"retryable", "recovery"}}`. Exit codes: 0 ok, 2 request/state, 3 conflict or lock,
4 I/O or damaged records, 5 unsupported version or Python.

## Commands

`S` below is the current `sessionId` from `packet.session.sessionId`.

### Workspace (allowed in any session state)

```json
{"command": "workspace.init", "expectedRevision": 0, "payload": {
  "goal": {"title": "…", "description": "…", "depth": "recognize|explain|derive|implement|apply"},
  "utcOffsetMinutes": 540, "learnerText": "background in the learner's words, or null to keep an existing learner.md"}}

{"command": "workspace.query", "expectedRevision": null, "payload": {
  "view": "resume|status|assessor|events|record|sources|knowledge|operation",
  "id": null, "search": null, "cursor": null, "limit": 20}}

{"command": "workspace.validate", "expectedRevision": null, "payload": {}}
{"command": "workspace.rebuild", "expectedRevision": N, "payload": {}}
{"command": "workspace.export", "expectedRevision": null, "payload": {
  "format": "markdown|json", "outputPath": "artifacts/summary.md", "overwrite": false}}
{"command": "source.register", "expectedRevision": N, "payload": {
  "relativePath": "materials/notes.md", "title": "…", "originKind": "local_file|url|model_generated", "origin": "…"}}
{"command": "knowledge.commit", "expectedRevision": N, "payload": {"extraction": {
  "scopeRefs": ["SourceRef, at least one"],
  "propositions": [{"localKey": "lower-slug", "name": "…", "statement": "…", "sourceRefs": ["at least one, inside scopeRefs"]}],
  "chains": [{"premises": [{"kind": "local", "id": "localKey"}, {"kind": "existing", "id": "propositionId"}],
              "conclusion": {"kind": "local", "id": "localKey"}, "sourceRefs": ["at least one, inside scopeRefs"]}],
  "identityLinks": [{"localKey": "…", "existingId": "propositionId", "reason": "…"}]}}}
```

Query views:

| view | id | Returns |
| --- | --- | --- |
| `resume`, `status` | null | The context packet: session, plans, progress, current question (without its answer key), hints, `nextAction` |
| `assessor` | null or the pending answerId | Full question with `expectedAnswer`, the answer, hints. Only while assessing or while the latest assessment can still be corrected |
| `events` | null or a sessionId | Event headers in order |
| `record` | an eventId | One lesson, answer, feedback, diagnosis or revealed solution as text |
| `sources` | null or a sourceId; `search` matches title/origin | Registered sources |
| `knowledge` | null or an ID; `search` matches name/statement | Propositions and chains |
| `operation` | an operationId | Whether that write was saved, its revision and entityIds |

Lists page with `limit` (1–100) and `cursor` = the previous `nextCursor`.

### Session

```json
{"command": "session.start", "payload": {"mode": "learning|practice|review", "startAt": "auto|replan",
  "targetNodeIds": [], "maxItems": null, "userText": "…"}}
{"command": "session.pause",  "payload": {"sessionId": "S", "userText": "…"}}
{"command": "session.resume", "payload": {"sessionId": "S", "userText": "…"}}
{"command": "session.finish", "payload": {"sessionId": "S",
  "outcome": "goal_demonstrated|partial|practice_done|review_done", "abandonPending": false, "userText": "…"}}
```

- Learning: `targetNodeIds: []`, `maxItems: null`. `startAt: "replan"` opens planning
  on an accepted plan.
- Practice/review: `startAt: "auto"`, `maxItems` 1–10, optional `targetNodeIds`.
- Finish: learning ends `goal_demonstrated` (only when the engine agrees) or
  `partial`; practice `practice_done|partial`; review `review_done|partial`. Set
  `abandonPending: true` only when a question, assessment, plan approval or
  repair is pending and the learner chose to stop anyway.

### Diagnosis and plan

```json
{"command": "diagnosis.complete", "payload": {"sessionId": "S", "summary": "…",
  "heldConcepts": ["…"], "gaps": ["…"], "evidenceAnswerIds": ["diagnostic answerIds"],
  "skipRequested": false, "userText": null}}

{"command": "plan.propose", "payload": {"sessionId": "S", "baseVersion": 0, "goalNodeId": "goal-node",
  "nodes": [{"nodeId": "lower-slug", "title": "…", "objective": "…", "depth": "explain",
    "prerequisites": ["earlier-node"], "criteria": [{"criterionId": "lower-slug", "description": "…"}],
    "sourceRefs": []}],
  "diagnosisSummary": "…", "revisionReason": null}}

{"command": "plan.accept", "payload": {"sessionId": "S", "version": 1, "userText": "learner's agreement"}}
```

- `baseVersion` is the latest proposed version (`0` for the first plan); read it
  from `packet.draftPlan` or `packet.acceptedPlan`.
- Nodes are listed so every prerequisite comes earlier, every node leads to the
  goal node, and at most 32 nodes. A nodeId once used keeps exactly the same
  content; changed content needs a new nodeId.
- Revising an accepted plan needs `revisionReason`.

### Questions and answers

```json
{"command": "question.pose", "payload": {"sessionId": "S", "question": {
  "purpose": "diagnostic|check|recheck|prerequisite_probe|transfer|practice|review",
  "nodeId": "currentNodeId or null for diagnostic", "planVersion": 1,
  "format": "open|single_choice|multiple_choice", "prompt": "…",
  "options": [], "selectionCriterionId": null,
  "expectedAnswer": "model answer, written before asking", "correctOptionIds": [],
  "criteria": [{"criterionId": "…", "description": "…"}],
  "lessonText": "explanation shown before a check, else null",
  "sourceRefs": [], "variationReason": null, "parentQuestionId": null}}}

{"command": "hint.record", "payload": {"sessionId": "S", "questionId": "Q",
  "kind": "cue|scaffold|partial_step", "text": "hint you will show", "userText": "learner's request"}}
{"command": "question.reveal", "payload": {"sessionId": "S", "questionId": "Q", "userText": "…"}}
{"command": "question.skip",   "payload": {"sessionId": "S", "questionId": "Q", "userText": "…"}}

{"command": "answer.record", "payload": {"sessionId": "S", "answer": {"questionId": "Q",
  "responseKind": "answer|dont_know", "text": "the learner's words", "selectedOptionIds": [],
  "thinking": null, "confidence": null, "reportedExternalHelp": "none|hint|solution|unknown"}}}
```

- `purpose` must equal `session.requiredMove.purpose`; `nodeId` must equal
  `session.currentNodeId`; non-diagnostic questions use the accepted plan's
  `version` and that node's exact `criteria`. Each `criterionId` appears once.
- `lessonText` is required for `check` and must be null for every other purpose.
- `transfer` is an open question on the goal node with a new prompt and a
  `variationReason`.
- Choice questions: 2–6 options with distinct `optionId`s, `correctOptionIds`,
  and `selectionCriterionId` naming the criterion the engine grades from the
  selected options. Open questions use `[]`, `[]`, `null`.
- `dont_know` answers use `confidence: null` and `selectedOptionIds: []`.
- `reportedExternalHelp` records what the learner said about outside help. Use
  `none` when they did not mention any (the default); `hint` or `solution` when
  they say they looked something up or saw an answer; `unknown` only when they
  say they are not sure whether they had help. The engine combines it with
  recorded hints and earlier reveals into `assistance`. Anything other than
  `none` keeps a correct answer from counting as independent.
- `text` is the learner's answer and `thinking` their stated reasoning, both in
  their own words. Do not split or rephrase beyond separating the two.

### Assessment and continuation

```json
{"command": "assessment.record", "payload": {"sessionId": "S", "assessment": {
  "answerId": "A", "replacesAssessmentId": null,
  "criterionResults": [{"criterionId": "…", "result": "met|not_met|unassessable", "evidence": "quote or point from the answer"}],
  "feedback": "what you will tell the learner", "errorStep": null, "sourceRefs": [],
  "issue": null, "changeReason": null}}}

{"command": "continuation.accept", "payload": {"sessionId": "S",
  "intent": "next|retry|skip_target|replan", "userText": "learner's choice"}}

{"command": "content.resolve", "payload": {"sessionId": "S", "assessmentId": "X",
  "resolution": "new_question|replan", "correction": "what was wrong", "sourceRefs": []}}
```

- Judge every criterion exactly once. The engine computes the verdict: any
  `unassessable` → `ungradable` (needs `issue`), all met → `correct`, all not met →
  `incorrect` (`not_recalled` for dont_know), otherwise `partial`.
- `issue` is `null` or `{"kind": "ambiguous_question|bad_source|bad_rubric",
  "description": "…"}`. `errorStep` is `null` or an integer ≥ 1.
- The selection criterion of a choice question must be what the selected options
  imply (`met` only for the exact correct set), or `unassessable` when the answer
  key is wrong.
- To correct the latest assessment before the learner continues, send a new
  assessment with `replacesAssessmentId` and `changeReason`.
- During diagnosis only `intent: "next"` is allowed; `replan` only in learning.
- `diagnosis.complete` is listed in every diagnosis state. Without an assessed
  diagnostic it needs `skipRequested: true` and the learner's words.

## Source references

```json
{"kind": "material", "sourceId": "…", "startLine": 3, "endLine": 5, "quote": "exact text inside those lines"}
{"kind": "lesson", "eventId": "…", "quote": "exact text from that lesson, feedback or revealed solution"}
```

## Error codes

| Code | Meaning | Recovery |
| --- | --- | --- |
| `INVALID_REQUEST` | Field, type, length or combination is wrong | Fix it; new `operationId` if the payload changes |
| `UNSUPPORTED_VERSION` | Protocol or journal format is newer | Stop; use a newer engine |
| `RUNTIME_UNSUPPORTED` | Python is older than 3.10 | Use Python 3.10+ |
| `WORKSPACE_MISSING`, `WORKSPACE_MISMATCH`, `WORKSPACE_NOT_EMPTY` | Wrong or unsuitable folder | Check the path and ID; never initialize over unrelated files |
| `REVISION_CONFLICT` | `expectedRevision` is stale | Query, then re-plan |
| `OPERATION_CONFLICT` | Same `operationId`, different request | New `operationId` |
| `LOCK_BUSY` | Another writer holds the folder | Wait, retry the same request |
| `INVALID_TRANSITION` | Not allowed in the current state or pending wait | Query `resume`; handle the pending item |
| `CONTENT_REPAIR_REQUIRED` | A repair is open | `content.resolve` first |
| `PLAN_REQUIRED`, `INVALID_PLAN`, `NODE_REDEFINED` | Plan missing or malformed | Fix the plan |
| `TARGET_NOT_ALLOWED`, `RUBRIC_MISMATCH`, `INVALID_ANSWER` | Question/answer/assessment does not fit the state or rubric | Follow `requiredMove`, `currentNodeId`, criteria |
| `HINT_LIMIT` | Three hints already | Offer answer, reveal or skip |
| `ASSESSMENT_FINALIZED` | Too late to correct that assessment | Check again in a new question |
| `INVALID_REFERENCE`, `SOURCE_CHANGED`, `PATH_OUTSIDE_WORKSPACE`, `FILE_EXISTS` | Citation, file or path problem | Fix the reference or path |
| `CONTEXT_LIMIT` | The packet would exceed 256 KiB | Shorten what you wrote; never shorten the learner's answer |
| `CORRUPT_JOURNAL` | Records are damaged | Stop writing; restore `records/events.jsonl` from a backup |
| `WRITE_FAILED`, `COMMIT_STATUS_UNKNOWN` | Disk problem | Query `view=operation` for that `operationId` before retrying |
