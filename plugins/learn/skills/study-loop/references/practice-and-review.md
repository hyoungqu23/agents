# Practice and review sessions

Separate sessions that exercise an accepted plan without teaching. Start one
when the learner asks to practice or review; a learning session must be
finished first. Payloads are in [protocol.md](protocol.md).

## Start

```json
{"command": "session.start", "payload": {"mode": "practice", "startAt": "auto",
  "targetNodeIds": [], "maxItems": 5, "userText": "learner's request"}}
```

- `targetNodeIds: []` lets the engine choose: nodes needing review (most recent
  failure first), then nodes whose last independent success is oldest. Name nodes
  only when the learner asked for them.
- `maxItems` 1–10: ask how many problems they want; 3–5 is a good default.
- Use `review` for recall of earlier material on a later day, `practice` for
  applying it.

## Each item

- `requiredMove.purpose` is `practice` or `review`; `lessonText` stays null.
  Write a problem on `currentNodeId`, with a new situation and a
  `variationReason` when the node was seen before.
- Answer, hint, reveal, skip and assessment work as in
  [teach-and-assess.md](teach-and-assess.md). Feedback can explain the error and
  show the expected answer after assessment.
- The engine's recommendation is `advance` (next item), `fresh_check` (another
  problem on this node) or `replan`. `next` follows it, `retry` stays on the node,
  `skip_target` moves on. `replan` is not available inside practice.

## When practice shows the plan is wrong

After repeated failures the engine recommends `replan`; a faulty rubric shows up
as a repair. Finish the session as `partial` (with `abandonPending: true` if a
repair is open), then start `{"mode": "learning", "startAt": "replan"}` and
propose the revised plan. Do not fake attempts to get past a bad question.

## End

When the queue is done, `offer_finish` appears. Summarize which nodes went
well without help and which need another look, then `session.finish` with
`practice_done` or `review_done`.
