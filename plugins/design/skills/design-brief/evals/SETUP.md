# Evaluator setup

Read this before launching the executor. Do not give it grading expectations.
Every `files` entry is a regular input file relative to this skill directory.

| Eval | Materialize the listed files | Before execution |
| --- | --- | --- |
| 1 | Strip `evals/files/existing-system/` from each path and copy beneath the disposable workspace | Record the initial contents of all four files |
| 2 | Copy `evals/files/new-brief.md` to `new-brief.md` | Create an empty `apps/reading/`; no design files or CSS |

Give the executor the workspace, prompt and input brief where applicable. Evaluate
only what the executor actually creates or changes.
