# Changelog

## 0.2.0 - 2026-11-12

- Add `think-through` for Socratic tutoring in the current conversation, with one question at a time and no learning-folder setup.
- Adapt the diagnostic and explanations to the learner; allow stopping at any point and describe demonstrated understanding without mastery scores.
- Route saved learning records and cross-session study to `study-loop`, and conversation-only tutoring to `think-through`.
- Preserve Jane Street's Socratic Tutor attribution and MIT notice, and add evaluation scenarios for scope, learner control, assistance and handoff.

## 0.1.1 - 2026-11-12

- Scope verbatim learner text to learner-authored fields; distinguish tutor hint text from the learner request and add a pending-question hint evaluation.

## 0.1.0 - 2026-11-06

- Add `study-loop`: diagnose, plan, teach, practice and review one goal over several sessions, waiting for the learner's real answers and choices.
- Keep the record in a local learning folder through a bundled, standard-library engine with a JSON contract, revisions, replayable operation IDs, an OS lock and crash recovery.
- Separate independent success from hinted, solution-seen and reported help; require a final independent transfer before a goal counts as demonstrated.
- Register materials as fixed copies, cite exact lines, and extract propositions and joint-premise chains on request without treating them as mastery.
- Resume the same folder from Claude Code or Codex; verified on macOS with both CLIs.
- Verify source snapshot hashes before accepting citations; reject aliased engine directories and preserve journals during exports and projection failures.
- Return structured corruption errors for malformed event containers and recover identity from the journal when projections are missing.
