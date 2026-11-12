# Learn

Two tutoring skills for different ways of studying:

| Skill | Use it for | Setup |
| --- | --- | --- |
| [`think-through`](skills/think-through/SKILL.md) | Learn through questions in the current conversation | None |
| [`study-loop`](skills/study-loop/SKILL.md) | Structured study, practice and review with a saved learning record | Python 3.10+ and a learning folder |

## Think Through

`think-through` helps you understand a topic by asking one question at a time,
checking your reasoning and adapting to your answers. Ask for a hint, a direct
explanation, a change in difficulty or a stop whenever you need one. It works
in the conversation without creating a folder or assigning mastery scores.

```text
Use $think-through to teach me closures through questions.
I know how functions work, but not what happens to their variables after a call.
```

Or in Korean:

```text
$think-through로 클로저를 질문하면서 가르쳐줘.
함수가 뭔지는 아는데, 호출이 끝난 뒤 변수는 어떻게 되는지 잘 모르겠어.
```

Ask to "save state" for a compact summary you can paste into another conversation.
It does not automatically persist progress or create `study-loop` records. For a
saved learning record across sessions, use `study-loop`.

## Study Loop

`study-loop` tutors one goal over several sessions. It finds where the learner
starts with a few diagnostic questions, agrees a small plan, teaches one step at a
time, waits for real answers and assesses them against rubrics written before each
question. Goals, answers, hints, progress and cited sources stay in a local
learning folder, so a new conversation in Claude Code or Codex continues where the
last one stopped.

```text
Use $study-loop to help me learn binary search well enough to explain it.
Keep my progress in ~/learning/binary-search.
```

## Installation

Claude Code also supports `/learn:think-through` and `/learn:study-loop`.
Install the plugin from this marketplace:

```text
/plugin install learn --marketplace hyoungqu23/agents
```

## Requirements

`think-through` has no runtime or learning-folder requirement.

`study-loop` runs its bundled engine, `scripts/study_loop.py`, with Python 3.10 or
newer and the standard library only. The macOS system `python3` is 3.9; the skill
looks for `python3.13` … `python3.10` and refuses to run on older Python rather
than misbehave. The host needs permission to run that script and to write the
learning folder.

## Study Loop learning folder

```text
my-learning/
├── learner.md            # background you can edit
├── materials/            # notes and documents you add (UTF-8 text or Markdown)
├── records/events.jsonl  # the record; one line per saved step
├── state.json, plan.md   # regenerated views
├── sessions/, knowledge/ # regenerated per-session logs and claims
├── sources/              # fixed copies of registered materials
└── artifacts/            # exports you ask for
```

The engine writes the record only through validated, revisioned steps, takes an
OS lock while writing, and never edits `learner.md` or `materials/`. One folder
holds one goal; start another folder for a different goal.

## Limits

- Neither skill certifies mastery or automatically schedules review.
- `think-through` summarizes only what the conversation shows, distinguishing
  independent answers from those reached with help. Its evaluation scenarios are
  in `skills/think-through/evals/evals.json`.
- `study-loop` progress means "shown once without help against this rubric," not
  long-term mastery. Its engine was verified on macOS with Claude Code and Codex
  CLI; Windows locking, desktop apps and Cowork have not been run.
- The `study-loop` engine's contract tests are `scripts/tests/test_study_loop.py`;
  they need Python 3.10+ and are skipped on older interpreters.
