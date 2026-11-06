# Learn

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

Claude Code also supports `/learn:study-loop`. Install the plugin from this marketplace:

```text
/plugin install learn --marketplace hyoungqu23/agents
```

## Requirements

The skill runs its bundled engine, `scripts/study_loop.py`, with Python 3.10 or
newer and the standard library only. The macOS system `python3` is 3.9; the skill
looks for `python3.13` … `python3.10` and refuses to run on older Python rather
than misbehave. The host needs permission to run that script and to write the
learning folder.

## Learning folder

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

- Progress means "shown once without help against this rubric," not long-term
  mastery. There are no mastery scores or automatic review schedules.
- Verified on macOS with Claude Code and Codex CLI. Windows locking, desktop apps
  and Cowork have not been run.
- The engine's contract tests are `scripts/tests/test_study_loop.py`; they need
  Python 3.10+ and are skipped on older interpreters.
