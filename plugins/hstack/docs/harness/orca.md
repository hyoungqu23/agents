# Orca adapter

Read this after [the Claude Code adapter](claude-code.md). Where the two disagree, this file wins.

hstack runs other vendors' models as Orca workers. It never runs a Codex or agy seat on the session model, so a review that should come from another vendor never comes from Claude.

## Skills that cannot run yet

`arena` and `swarm` start panels of workers, and hstack has not adapted all of their steps yet. When either is invoked, stop before its first step and tell the user that it is unavailable until hstack adapts it. Do not start subagents or workers for it. `interrogate` runs, as Panels says.

When another skill routes a step to either of them, do not do that step another way. What happens next depends on whether a later step needs what the skipped step makes:

- Nothing later needs it: put one line in your reply, `Skipped in hstack: <step>. <skill> is not available yet.`, and go on to the next step.
- A later step needs it, as with the code that the Feature playbook delegates to `arena` when the implementation admits several shapes, or the Eval playbook's candidates and judge: stop the playbook at that step. Tell the user which step needs which skill, and report what the earlier steps finished. Do not go on to the steps that would check, ship or score the missing output.

A skill that only names one of them, as `poteto-help` does in its tables and recipes, still runs. When it suggests that the user type one of them, say that it is not available yet.

## Names

This plugin is installed as `hstack`, not `pstack`.

| Claude Code adapter | Here |
| --- | --- |
| `/pstack:<name>` when you tell the user what to type | `/hstack:<name>` |
| `<pstack>`, the plugin folder | The hstack plugin folder, two levels above a skill's `SKILL.md`. `<hstack>` below is the same folder |
| Install with `/plugin marketplace add cursor/plugins` and `/plugin install pstack@cursor-plugins` | Never suggest it. hstack is already installed, and pstack would run without this file. |
| `pstack:poteto-agent`, `pstack:comment-sicko` as `subagent_type` | Neither is registered. `Read` `<pstack>/upstream-agents/<name>.md`, start a `general-purpose` agent, and put that file's body at the top of its brief. Ignore the file's `model:` line. |

## Skills that are not installed

`make-bot-ui`, `statechart`, `create-formal-verification-skill` and `maintain-formal-verification-skill` are not part of hstack. Where a skill offers or calls one of them, say that hstack does not include it and continue without it.

| Skill named | Here |
| --- | --- |
| `/deslop` from `cursor-team-kit` | Skip with the line `Skipped in hstack: /deslop. hstack has no equivalent.` |
| `control-ui` or `control-cli` from `cursor-team-kit` | The `build:dogfood` skill when it is installed. Otherwise skip with the line |

## Seats

hstack keeps pstack's role names and gives each role seats instead of model slugs. A seat is a CLI and, for most CLIs, a model:

| Seat | Runs on |
| --- | --- |
| `claude <model> [<effort>]`, such as `claude claude-opus-5-5 xhigh` | Claude Code. `<model>` is a full Claude model id |
| `codex [<model> [<effort>]]` | Codex. With no model, Codex's own configuration decides |
| `agy <model>`, such as `agy gemini-4-neon-xhigh` | agy. Only `gemini-*` ids without `orchestrator`. The effort is part of the id |

The seats live in `~/.config/hstack/seats.md`, one `role: seat, seat` line per role. A role without a line takes its default. Neither `~/.claude/rules/pstack-models.md` nor `~/.cursor/rules/pstack-models.mdc` is read or written. To see every role's seats, run:

```sh
python3 <hstack>/scripts/hstack_seats.py seats
```

`agy fallback` is hstack's own role: the agy seat to use when an agy seat stopped on its usage limit. It starts as another attempt at the same Task, in the same run record:

```sh
python3 <hstack>/scripts/hstack_seats.py start --role <role> --worktree <selector> --fallback --task <task> --retry-of <failed dispatch> --record <record>
```

Add `--index` when the role has more than one agy seat.

## Models

These rows replace the Claude Code adapter's Models table and every skill's rules for picking a slug.

| pstack | Here |
| --- | --- |
| The role lines in `pstack-models.mdc` or `pstack-models.md`, and the skill's default slug for a role | The role's seats from `hstack_seats.py seats`. There is no `# defaults` line, so never tell the user to rerun `setup-pstack` for one |
| A subagent for a role whose seat is `claude <model> <effort>`, outside a panel | An `Agent` call with `model` set to the id's family (`claude-opus-5-5` is `opus`, `claude-fable-5-2` is `fable`, and likewise `sonnet` and `haiku`) and `effort` set to the seat's effort. Raise or lower the effort for the job as the skill says |
| A subagent for a role whose seat is `codex` or `agy` | One Orca worker on that seat. See Workers |
| A panel seat of `arena runners` or `interrogate reviewers`, whatever its CLI | One Orca worker on that seat. See Panels |
| A second opinion "on another vendor's model", and the cross-model review in `show-me-your-work` | One Orca worker from the `arena cross-judge pool` role. `start` without `--index` picks the pool's first seat that is not `claude` |
| `-fast`, and "use the nearest valid slug of the same family" when a slug is rejected | Do not apply. When `start` refuses a seat, report the refusal. Never fall back to the session model |
| `reviewed by <model>` | The seat as the seats file writes it, such as `reviewed by codex` or `reviewed by agy gemini-4-neon-xhigh` |

## Workers

Follow Orca's own guide for everything after a worker starts: ending your turn, being woken, reading messages, answering questions and handling escalations. Run `orca skills get orchestration` once per session before the first worker and follow it, except where this section says otherwise.

### Before the first step

Before the first step of a playbook, check every role that has a `codex` or `agy` seat and that the playbook will start as a worker, including `arena cross-judge pool` when it asks for a second opinion or runs `show-me-your-work`:

```sh
python3 <hstack>/scripts/hstack_seats.py preflight --role <role> [--role <role> ...] [--reads <path> ...]
```

When it prints a problem, show it and stop before the first step, so no work is done that a worker would then fail to review. A playbook that starts no worker needs no preflight.

### Starting

Start every worker with `hstack_seats.py start`. Never call `orca orchestration worker-start` yourself, because only `start` checks the seat and records the request first.

```sh
python3 <hstack>/scripts/hstack_seats.py start --role <role> --worktree <selector> \
  --spec-file <spec> --instructions <hstack>/skills/poteto-mode/worker.md \
  --task-title <title> --record <record>
```

- Write the spec to a file first, under the run record's folder, not the repository. Make it stand alone: the goal, the scope, what the worker may edit, and the evidence that proves it is done.
- `--instructions` replaces the kickoff line `Read <path>/worker.md before anything else.` that `poteto-mode` asks for. Do not also write that line into the spec.
- `--worktree current` for a worker that only reads. A worker that writes gets its own: `--worktree new-child --name <short-name>`. Its spec tells it to commit there and to report the worktree path, branch and commits. Its changes are not in your checkout, so before a later step reproduces, checks, stages or commits them, bring the commits in with `git cherry-pick`, or run that step in the worker's worktree.
- Use one `--record` file for the whole run. A new run gets a path that does not exist yet, such as `~/.local/state/hm2/hstack/runs/<date>-<HHMMSS>-<slug>.json`. `start` joins the Run an existing record names, so reuse a path only to resume that run. Add `--run <run id>` only when this session is bound to another Run.
- An agy worker reads nothing outside its own workspace without asking. Pass every other path it must read with `--reads`. When `start` refuses those reads, start another seat of the role with `--index` or report that the step did not run.
- Keep at most four workers open at once.

| `start` exit code | Meaning | Do |
| --- | --- | --- |
| 0 | Started | End your turn. Orca wakes you |
| 1 | Did not start | Report the stage and error it printed |
| 2 | Refused before starting anything | Fix the arguments, or report what it named. Do not try another way |
| 3 | Unknown whether it started | Do not start it again. See Resuming |

### Dropouts

- When an agy worker stops on its usage limit, confirm that its Dispatch failed, release it (`orca orchestration worker-release --dispatch <dispatch id> --environment local`), then start the `agy fallback` seat once as another attempt at the same Task. A second failure on the same seat is a dropout. A `claude` or `codex` seat has no fallback, so its usage limit is a dropout.
- A worker waiting for its quota window is not a dropout. Tell the user.
- When a seat drops out and another vendor's seat still reports, go on and name the dropped seat in the result.
- When every other vendor's seat drops out, end the step unfinished. Never report a review or a cross-check that did not run as done.

### Finishing

- Release a finished worker that is still open once the step that used it is done and you have read what you need from it.
- Ask the user before deleting a worker's worktree. An unpicked candidate's changes live only there.
- List the released workers and the kept worktrees in the final report.

### Resuming

The run record holds each start's request id, Task id, Dispatch id and status. When you come back to a run:

1. For each seat whose status is `unknown`, run `orca orchestration request-show --request <request id> --environment local --json`. `start` runs on the local Orca, so ask the same one. This needs no Run, so it works when the first start lost its response and the record's `run_id` is still empty.
   - `completed`: Orca recorded an outcome, which may be a failure. Read its `receipt`. Fill the record with it: started when `state` is `ready`, otherwise failed or unknown as the outcome says. Take the Run from `runId` when the record has none.
   - `pending`: the start is still running or was cut off. Wait for it if it runs. Otherwise follow Orca's recovery steps with that request id. Do not call `start` again, because it makes a new request id.
   - `absent`: not proof that nothing started. A first start has a `task_title` in the record: look for that Task in the record's Run with `task-list`, or, when the record has no Run, in each recent Run from `run-list`. A fallback start reuses the Task, so its title proves nothing: run `dispatch-show --task <task id> --environment local --json` and take its `dispatch` only when its `retry_of_dispatch_id` is the record's `retry_of`. Any other Dispatch, or none, does not identify this attempt. If you find the worker, fill the record. Otherwise keep the seat `unknown`, report it as unconfirmed and do not start it again.
2. Bind to the record's Run: `orca orchestration run-use --id <run id> --environment local`. When no Run was found, skip this step only. A seat that is still `unknown` stays unconfirmed in the record and in your report.
3. Match the other seats with the Run's workers and your messages.

## Panels

A panel runs one worker per seat of a role: `arena runners` for `arena`, `interrogate reviewers` for `interrogate`. Every seat, `claude` seats included, runs as an Orca worker through `start`, so one record, one resume and one cleanup cover the whole panel. These rules replace arena Phase A steps 3 and 4 and Phase B.

### Seats

1. Run `python3 <hstack>/scripts/hstack_seats.py preflight --role <role>` before anything else. When it prints a problem, show it and stop.
2. Start one worker per seat, in the order `seats` prints them, with `--index <n>`. Do not add or repeat seats. Keep at most four open: when a role has more seats, start the rest as earlier workers report and are released.
3. A seat that `start` refuses or fails to start is a dropout, and so is a seat that drops out later as Dropouts says. Go on while two seats remain and one of them is `codex` or `agy`. Otherwise end the skill unfinished: release the workers that have finished, and stop the ones still running with `orca orchestration worker-stop --dispatch <dispatch id> --environment local`.

### Worktrees

Each seat works in its own worktree, which you create before the start so the worker finds the changes in its own workspace. An agy worker then needs no `--reads`.

For `interrogate`, freeze the scope once, before the first seat, so every seat reviews the same changes even when a seat waits for a free slot. `arena`'s candidate worktrees are adapted with the rest of `arena`.

1. Write `<paths>` relative to the top of your checkout: the paths the user named, each prefixed with `git rev-parse --show-prefix` when you are in a subfolder, or `.` when the scope is the whole branch. Use the same `<paths>` in the spec.
2. Save the commit, the tracked changes and the untracked files under `<snapshot>`: the run record's path without `.json`, plus `-scope`, as an absolute path. A new run's record is new, so `mkdir` without `-p` refuses a folder an earlier run left. The `&&` stops at the first command that fails:

   ```sh
   cd "$(git rev-parse --show-toplevel)" &&
   mkdir -p "$(dirname <snapshot>)" &&
   mkdir <snapshot> <snapshot>/files &&
   git rev-parse HEAD > <snapshot>/head &&
   git diff --binary "$(cat <snapshot>/head)" -- <paths> > <snapshot>/tracked.patch &&
   git ls-files --others --exclude-standard -z -- <paths> > <snapshot>/untracked &&
   rsync -a --from0 --files-from=<snapshot>/untracked ./ <snapshot>/files/
   ```

   When it fails, report the command and its output and start no seat. A symbolic link whose target is missing is known to fail here.

Then, for each seat:

1. Name its worktree `<slug>-<label>-<letter>`, such as `login-retry-adversary-a`: `candidate` for `arena`, `adversary` for `interrogate`, and letters in seat order. Never put a CLI, vendor or model in the name. Which seat has which letter is written only in the run record.
2. Create it from the saved commit:

   ```sh
   orca worktree create --environment local --name <name> --base-branch "$(cat <snapshot>/head)" --parent-worktree current --json
   ```

3. Copy the saved changes in and stage them. `apply --index` stages the tracked changes, deletions and files added with `git add -f` included. The `add` line stages the untracked files; `-f` keeps a `.gitignore` change outside `<paths>` from blocking them. The last line saves what the seat was given, which Verify compares with:

   ```sh
   git -C <worktree> apply --index --allow-empty <snapshot>/tracked.patch &&
   rsync -a --from0 --files-from=<snapshot>/untracked <snapshot>/files/ <worktree>/ &&
   git -C <worktree> add -f --pathspec-from-file=<snapshot>/untracked --pathspec-file-nul &&
   git -C <worktree> write-tree > <snapshot>/<letter>.tree
   ```

   When it fails, do not start the seat. Report the command and its output, then compare `git -C <worktree> status` with yours and fix the copy by hand, or treat the seat as a dropout. A rename that changes only letter case is known to fail here.

4. Start the seat in it with `--worktree path:<worktree>`.

### Spec

Write the spec as Workers says. Leave out `--instructions`: a panel worker follows its own brief, not `worker.md`. For `interrogate`, give it the scope's base commit and `<paths>`: the merge base of the saved commit with the base branch (`git merge-base <base branch> "$(cat <snapshot>/head)"`) when the scope is the branch, or the saved commit when it is only uncommitted work. Tell it that the commits and the copied changes are already in its worktree, so `git diff --cached <base commit> -- <paths>` shows the whole scope. Tell it to report with `worker_done`.

### Verify

Rerun each reported command yourself in that seat's worktree, where its repros are, after the worker reports. Read the output yourself; a worker's description of its output is not evidence.

First list what the worker changed in its worktree since it was given the scope, commits included:

```sh
git -C <worktree> add -A && git -C <worktree> diff --cached --name-status "$(cat <snapshot>/<letter>.tree)"
```

A failure that needs one of those changes to the code under review is the worker's, not the scope's: keep the finding only when the command runs the scope's code as it was given, plus repro scripts and tests the worker added. Otherwise report it as unverified.

The command and the files it runs were written by the worker, and a rerun runs them with your permissions. Before each rerun, read the command and every script, test or fixture it runs that the worker added or changed. Rerun only with your session's sandbox on. Never turn it off for a rerun. A finding whose command reaches the network, reads credentials, writes outside the worktree, or cannot run inside the sandbox stays unverified: report it as unverified, not as verified or dropped.

### Finishing

Release a panel worker once it has reported and you have read its report. Its worktree stays, so Verify can still rerun its commands there. Release the dropouts too, as Dropouts says. Ask before deleting the worktrees, and list them in the report with each letter's seat.

## interrogate

Follow the skill with Panels. Its "Run Phase A steps 3 and 4 and Phase B of the **arena** skill" means Panels' Seats, Worktrees and Spec with `interrogate reviewers`. Copying the scope's uncommitted changes is the snapshot and the per-seat copy in Worktrees. "Spawn each adversary as `generalPurpose`" is the Orca worker. The brief goes in the spec word for word, after the scope and the intent.

Its Verify step reruns each finding as Panels' Verify says. Add an **Unverified** list to the output for the findings that Verify could not rerun, each with the reason. In the output, name each adversary by its seat as the seats file writes it, such as `codex` or `agy gemini-4-neon-xhigh`.

## setup-pstack

Follow the skill with these changes. They replace the Claude Code adapter's section on it.

- Detect. Claude seats take full model ids that this Claude Code can run, such as `claude-opus-5-5` and `claude-fable-5-2`. agy seats take the ids `agy models` lists, and only `gemini-*` ids without `orchestrator`. Leave Codex seats without a model unless the user names one. The aliases `inherit-parent` and `auto` are not seats: do not offer or write them.
- Load. Read `~/.config/hstack/seats.md` if it exists. There are no old defaults to replace and no `# defaults` line. A line whose role `hstack_seats.py` does not know is dropped; tell the user.
- Defaults. The defaults are what `python3 <hstack>/scripts/hstack_seats.py seats --defaults` prints. On a later run, compare each role in the file with them to tell which roles the user changed. Every panel role (`arena runners`, `arena cross-judge pool`, `interrogate reviewers`) keeps at least one `codex` or `agy` seat, because the coordinator is a Claude session and its judge or reviewers must be another vendor. `arena runners` and `interrogate reviewers` keep at least two seats.
- Budget. Move the effort of each `claude` and `codex` seat that names one, and the effort suffix of each `agy` id to an id `agy models` lists. Families are CLIs.
- Validate. Write the file, then run `python3 <hstack>/scripts/hstack_seats.py validate`. Fix every line it reports and run it again until it passes.
- Write. No frontmatter. Comment lines first, then the `# budget` line, then one line per role in the order `seats` prints them. Leave out the `agy fallback` line when no other role has an `agy` seat, so a machine without agy can pass `validate`. Overwrite the whole file.
- Steps 7 and 8. Offer step 7. Skip step 8: hstack does not include `create-formal-verification-skill`.
