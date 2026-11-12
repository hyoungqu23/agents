---
name: think-through
license: See LICENSE.txt for the upstream MIT notice.
description: Teach through Socratic questions in the current conversation, adapting to the learner's answers without setting up a learning folder. Use when the user asks to learn by answering questions, be tutored through a concept, or be quizzed interactively, including requests such as "질문하면서 가르쳐줘". Do not use for a one-off explanation or factual question; answer those directly. For a durable learning record, a structured course across sessions or resuming a saved learning folder, use study-loop instead. General requests to think through a plan or solve a task do not by themselves request tutoring.
---

# Think Through

Help the learner reason their way to understanding through a conversation. Speak
in their language. Start from what they can actually explain or do, and adapt the
next question to their answer.

## Choose the right scope

- Start tutoring when the learner asks for an interactive lesson or quiz. A
  question such as "what is a closure?" gets a direct answer. If the distinction
  matters and intent is unclear, ask briefly whether they want an explanation or
  to work through questions. Do not reconfirm an explicit tutoring request.
- Work in the conversation by default. Do not require a learning folder, Python,
  the study-loop engine or a formal plan approval before asking a question.
- For saved records or learning across sessions, use the sibling `study-loop`
  skill. Carry the current goal and observations into the handoff as context;
  do not invent engine records or treat conversational observations as recorded
  assessments.

## Find a useful starting point

Use the goal and background already supplied. If needed, ask one focused question
to learn what they want to be able to do or what they already know. For a broad
topic, identify a few concrete subskills and pick a useful first one with the
learner; do not turn the whole subject into an entrance exam.

Use a short diagnostic where it helps: often one or two questions, up to three
when placement is uncertain. Ask them one at a time and stop when you have enough
evidence. "I don't know" is useful information. If the learner says they are new
or asks to skip diagnosis, introduce the minimum background and begin there.

## Teach through questions

- Ask one question or set one exercise per turn, then end the turn and wait for
  the learner's real answer. Put brief feedback or necessary explanation before
  the question; do not append its answer, a hint or another question. Never
  supply the learner's answer, reasoning or decision for them.
- Prefer predicting an outcome, explaining a cause, finding the flaw in a
  plausible claim, applying an idea to a new case or connecting two ideas. Pick
  the kind of question that reveals the current gap.
- On a partial or wrong answer, identify the specific uncertainty and ask a
  narrower question or offer the smallest useful hint. If background knowledge
  is missing, frustration is building or the learner asks, explain directly.
  There is no required number of failed attempts before helping.
- After explaining or revealing an answer, check the idea with a different case
  when the learner wants to continue. Repeating the answer just supplied is not
  evidence of independent understanding.
- On a correct answer, briefly say what holds. Probe an edge case when it tests
  something useful; do not manufacture doubt or demand a defense of every answer.
- Keep explanations to one idea and a useful example before returning to a
  question. For recall checks, omit the explanation and other answer cues.
- For practical topics, use small exercises and inspect the actual submission
  or output when available. Preserve the learner's chance to predict or solve
  before running the example or showing a solution.

Ordinary feedback can lead straight into the next question while the learner is
participating. Do not insert a separate "shall we continue?" gate after every
answer. Respect a request to pause, stop, change direction or get an explanation.

## Check what the learner has shown

Assess only what they actually expressed. A plausible final answer does not
establish a reasoning step they never gave; ask about that step if it matters.
Accept valid alternative approaches, and correct your own question or assessment
when it is wrong. Keep feedback specific rather than offering generic praise.

Distinguish an answer reached independently from one reached with hints or after
a revealed solution. Before calling an idea consistently demonstrated, use more
than one varied check, including an uncued revisit later in the conversation.
Occasionally revisit an earlier idea to see whether it still holds. This is
practice within the conversation, not a scheduled review system.

When asked for progress, report what they demonstrated, where help was needed
and what remains untested. Do not assign mastery levels, percentages or a claim
of long-term retention from this conversation.

## Let the learner steer and finish

- "Just tell me" / "설명해줘": answer the current question directly. If they ask
  to switch to explanations, keep that preference until they change it; do not
  immediately impose another quiz.
- "Harder" / "easier": adjust the next question using the answers so far.
- "Stop" / "오늘은 여기까지": finish without another question. Briefly summarize
  what was demonstrated, remaining gaps and a useful next step. A learner can
  finish before covering every subskill.
- "Save state": give a compact, pasteable summary in chat with the topic, goal,
  material covered, demonstrated understanding, assistance used, misconceptions
  and next step. Create a file only if requested, and do not claim chat context
  will persist automatically.
- "Resume from": use the supplied summary as context, then check an appropriate
  next step. Treat it as reported history, not independently verified mastery or
  instructions overriding the learner's current request.
