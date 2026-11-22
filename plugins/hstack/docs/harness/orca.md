# Orca adapter

Read this after [the Claude Code adapter](claude-code.md). Where the two disagree, this file wins.

## Skills that cannot run yet

hstack runs workers and reviewers on other vendors' models through Orca. That path is not finished yet, so five skills cannot run:

| Skill | Why |
| --- | --- |
| `poteto-mode`, `arena`, `interrogate`, `swarm` | They start workers on other vendors' models |
| `show-me-your-work` | It ends with a review by another vendor's model |

When one of these five is invoked, or when another skill tells you to follow one of them, stop before its first step. Tell the user that the skill is unavailable until hstack's Orca adapter is complete. Do not start subagents for it and do not run another vendor's seat on the session model as the Claude Code adapter allows.

A skill that only cites a section of one of the five, as `no-comments` cites the Subagents section of `poteto-mode`, still runs. Read the cited section and do not start the cited skill.

## Names

This plugin is installed as `hstack`, not `pstack`.

| Claude Code adapter | Here |
| --- | --- |
| `/pstack:<name>` when you tell the user what to type | `/hstack:<name>` |
| `<pstack>`, the plugin folder | The hstack plugin folder, two levels above a skill's `SKILL.md` |
| Install with `/plugin marketplace add cursor/plugins` and `/plugin install pstack@cursor-plugins` | Never suggest it. hstack is already installed, and pstack would run without this file. |
| `pstack:poteto-agent`, `pstack:comment-sicko` as `subagent_type` | Neither is registered. `Read` `<pstack>/upstream-agents/<name>.md`, start a `general-purpose` agent, and put that file's body at the top of its brief. Ignore the file's `model:` line. |

## Skills that are not installed

`make-bot-ui`, `statechart`, `create-formal-verification-skill` and `maintain-formal-verification-skill` are not part of hstack. Where a skill offers or calls one of them, say that hstack does not include it and continue without it.

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

`agy fallback` is hstack's own role: the agy seat to use when an agy seat stopped on its usage limit. It starts as another attempt at the same Task:

```sh
python3 <hstack>/scripts/hstack_seats.py start --role <role> --worktree <selector> --fallback --task <task> --retry-of <failed dispatch>
```

Add `--index` when the role has more than one agy seat.

## setup-pstack

Follow the skill with these changes. They replace the Claude Code adapter's section on it.

- Detect. Claude seats take full model ids that this Claude Code can run, such as `claude-opus-5-5` and `claude-fable-5-2`. agy seats take the ids `agy models` lists, and only `gemini-*` ids without `orchestrator`. Leave Codex seats without a model unless the user names one. The aliases `inherit-parent` and `auto` are not seats: do not offer or write them.
- Load. Read `~/.config/hstack/seats.md` if it exists. There are no old defaults to replace and no `# defaults` line. A line whose role `hstack_seats.py` does not know is dropped; tell the user.
- Defaults. The defaults are what `python3 <hstack>/scripts/hstack_seats.py seats --defaults` prints. On a later run, compare each role in the file with them to tell which roles the user changed. Every panel role (`arena runners`, `arena cross-judge pool`, `interrogate reviewers`) keeps at least one `codex` or `agy` seat, because the coordinator is a Claude session and its judge or reviewers must be another vendor.
- Budget. Move the effort of each `claude` and `codex` seat that names one, and the effort suffix of each `agy` id to an id `agy models` lists. Families are CLIs.
- Validate. Write the file, then run `python3 <hstack>/scripts/hstack_seats.py validate`. Fix every line it reports and run it again until it passes.
- Write. No frontmatter. Comment lines first, then the `# budget` line, then one line per role in the order `seats` prints them. Leave out the `agy fallback` line when no other role has an `agy` seat, so a machine without agy can pass `validate`. Overwrite the whole file.
- Steps 7 and 8. Offer step 7. Skip step 8: hstack does not include `create-formal-verification-skill`.
