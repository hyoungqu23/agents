# Teach, ask and assess

Covers `present_and_check`, `await_answer`, `assess_answer`, `wait_for_continue`
and `repair_content` in learning sessions. Payloads are in [protocol.md](protocol.md).

## Pick the question from `requiredMove`

| `requiredMove` | Write |
| --- | --- |
| `check` + `initial_explanation` | A short explanation of the node (`lessonText`), then one question on it |
| `check` + `targeted_repair` | Name the specific error from the last answer, explain that point only, ask a different question on the same node |
| `check` + `alternative_explanation` | Explain the node another way (new example, picture, analogy), then ask |
| `recheck` | A new question on the same node with no explanation (`lessonText: null`); change numbers or situation and say how in `variationReason` |
| `prerequisite_probe` | A question on the prerequisite node in `currentNodeId`, without teaching |
| `transfer` | An open question on the goal node in a new situation, with `variationReason` |

Keep `lessonText` brief: one idea, one example. Write `expectedAnswer` and the
criteria-based answer key before you ask. Do not change them after the learner
answers; if they were wrong, assess `unassessable` with an `issue` and repair.

Ask one question per turn. Show `lessonText`, then the prompt and options, and
stop. Invite reasoning and confidence ("어떻게 생각했는지, 얼마나 확신하는지도
적어 주면 좋아요") but accept a bare answer.

## While waiting (`await_answer`)

- A hint request: write the smallest useful hint and record it with
  `hint.record` before showing it. Escalate across requests: `cue` (where to
  look) → `scaffold` (a step or sub-question) → `partial_step` (part of the
  work). Three hints at most.
- "정답 보여줘": `question.reveal`, then show `packet.revealedSolution`.
- "넘어가자": `question.skip`.
- An answer: record it verbatim with `answer.record`. `reportedExternalHelp` is
  `none` unless the learner says they looked something up or got help (`hint`,
  `solution`) or are unsure (`unknown`). Do not guess `unknown` from silence.

## Assess (`assess_answer`)

Query `view=assessor` to see the answer key, then judge each criterion from what
the learner actually wrote:

- `met` / `not_met` with `evidence` pointing to their words. A different valid
  method that satisfies the criterion is `met`; do not require the model wording.
- A right final answer with wrong or missing reasoning fails the reasoning
  criterion.
- `unassessable` only when the question, rubric or material is at fault, with an
  `issue` (`ambiguous_question`, `bad_source`, `bad_rubric`).
- `errorStep` is the first step where their reasoning went wrong, when you can
  point to one. Never invent reasoning they did not write.

Feedback (`feedback`) for the learner:

- Start with what was right, then the first real error and why it matters.
- If they were confident (`confidence` ≥ 80) and wrong, say plainly that this is
  a misconception worth fixing; if unsure and right, say their reasoning holds.
- No score, no judgment of ability. The verdict is the model's assessment
  against the rubric, not a certified fact.

If you notice your assessment was wrong before the learner continues, send a
corrected `assessment.record` with `replacesAssessmentId` and `changeReason`.

## Continue (`wait_for_continue`)

Explain `recommendedMove` in plain words and offer the choices:

| recommendedMove | Meaning to the learner |
| --- | --- |
| `advance` | 다음 단계로 |
| `fresh_check` | 도움 없이 새 문제로 한 번 더 확인 |
| `targeted_repair` | 틀린 부분만 짚고 다른 문제 |
| `prerequisite_probe` | 앞 단계를 먼저 확인 |
| `alternative_explanation` | 다른 방식으로 다시 설명 |
| `replan` | 계획을 고치기 |
| `finish` | 목표를 보였으니 마무리 |

Send `continuation.accept` with the learner's choice: `next` follows the
recommendation, `retry` asks again on the same node, `skip_target` sets this
node aside for this session, `replan` reopens planning. Do not start the next
question until they answer.

A success after a hint or a revealed solution is not independent: the engine
asks for a fresh check before the node counts as demonstrated. Do not describe
it as mastered.

## Repair (`repair_content`)

Say what was wrong with the question or material, then `content.resolve`:
`new_question` discards the faulty question and continues on the same node;
`replan` (learning only) reopens the plan when the rubric or node itself is
wrong.

## Finishing a goal

After every node is demonstrated, the engine asks for one independent transfer
question on the goal node. Only after that does `offer_finish` allow
`goal_demonstrated`. Even then it means "shown once without help," not long-term
mastery; suggest a later review session.
