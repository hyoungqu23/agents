# Diagnose and plan

Find where the learner starts, then agree a small plan toward the goal. Read
[protocol.md](protocol.md) for payload shapes.

## Before the first session

Ask, in one short message, for what you do not already know:

- The goal as an observable action: recognize, explain, derive, implement or
  apply something. This becomes `goal.depth`.
- Background and what they already tried. This becomes `learnerText`; the
  learner can edit `learner.md` later.
- Materials they want to study from (see
  [sources-and-knowledge.md](sources-and-knowledge.md)).

Do not ask for confidence ratings, scores or personal data the plan does not need.

## Diagnosis (`ask_diagnostic`)

- Ask at most three diagnostic questions; the engine refuses a fourth. One or two
  are often enough.
- Each probes a prerequisite or the goal itself at the target depth. Prefer
  questions that make the learner show reasoning ("왜 그런가?"), not recall.
- Do not teach during diagnosis: `lessonText` is null and feedback stays short
  ("이 부분은 이미 알고 있네요", "이건 계획에 넣을게요").
- `dont_know` is a valid, useful answer. Say so before the first question.
- After feedback, continue with `continuation.accept` `intent: "next"` for the
  next diagnostic, or go straight to `diagnosis.complete` when you know enough.
- If the learner asks to skip diagnosis, send `skipRequested: true` with their
  words in `userText`. This is always allowed during diagnosis. When every
  diagnostic was revealed or skipped, ask whether to plan without one; a
  `diagnosis.complete` without `skipRequested` needs at least one assessed answer.

`diagnosis.complete`: `summary` is what the answers showed, not a judgment of
the person. `heldConcepts` and `gaps` are short phrases. `evidenceAnswerIds` are
the diagnostic answers you relied on.

## Plan (`propose_plan`, `await_plan_approval`)

- 2–7 nodes is typical; 32 is the hard limit. Each node is one teachable step
  with an `objective` the learner can demonstrate.
- `criteria` are what an answer must show, one observable property each, such as
  "states the sum" and "explains why combining counts gives the sum". Two to four
  per node. Questions on that node reuse exactly these criteria.
- List prerequisites before the nodes that need them. Every node must lead to
  `goalNodeId`, and nodes the learner already showed in diagnosis can be left out.
- `diagnosisSummary` ties the plan to the diagnosis evidence.

Save the plan with `plan.propose` first, then show `packet.draftPlan` as a short
numbered list (title, what they will be able to do). Ask for agreement or
changes. Record agreement with `plan.accept`, the draft's `version` and their
words. If they ask for changes, send a revised `plan.propose` with
`baseVersion` = the draft's version and show the new draft.

## Replanning later

When the engine recommends `replan`, or the learner wants to change the route:
accept the continuation with `intent: "replan"` (learning sessions), then propose
the revision with `revisionReason`. Keep unchanged nodes' IDs and content; give
changed nodes new IDs. Progress carries over only for identical nodes.

A different goal is a different folder, not a replan.
