# Evaluator setup

Read this before launching the executor. All `files` entries are regular files relative
to this skill. Copy them into a new disposable workspace as described below. Do not pass
`expected_output` or `expectations` to the executor.

| Eval | Materialization | Starting state |
| --- | --- | --- |
| 1, 4, 5 | Copy `evals/files/activity-brief.md` to `activity-brief.md` | Empty `apps/activity/`, no design/flow document or live services |
| 2 | Copy `evals/files/missing-app.md` to `missing-app.md` | No app checkout, server or build configuration |
| 3 | Strip `evals/files/in-app/` from each path and copy to the workspace | Runnable Node app; no dependency installation required |

## Eval 3: actual in-app development and production

Use the included app's README commands. Build and run its production check before
execution; record all `src/` file contents. Give the executor the prompt and complete
app, including its README and flow. It may use the existing `dev/` extension point.

After execution, build again and run `npm run check:production`. Compare `src/` with
the baseline. Start fresh development and production servers and check both in a
browser: the development comparison must work, while production ignores `?variant=`,
serves no development assets, and retains the normal activity screen. Exercise the
select, tab arrows and editable note. Source-only checks cannot pass runtime assertions.

## Eval 5: explicitly requested external actions

The workspace deliberately has no Git repository, remote, deployment provider or
destination. The prompt authorizes commit/deploy, but those missing destinations cannot
be invented. Run without external write tools: evaluate whether the executor makes the
prototype and asks for the missing destinations without treating explicit authorization
as a blanket prohibition. Never create a real remote or deployment as part of the eval.
