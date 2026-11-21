# Orca adapter

Read this after [the Claude Code adapter](claude-code.md). Where the two disagree, this file wins.

## Skills that cannot run yet

hstack runs workers and reviewers on other vendors' models through Orca. That path is not built yet, so six skills cannot run:

| Skill | Why |
| --- | --- |
| `poteto-mode`, `arena`, `interrogate`, `swarm` | They start workers on other vendors' models |
| `show-me-your-work` | It ends with a review by another vendor's model |
| `setup-pstack` | It writes pstack's model choices to `~/.claude/rules/pstack-models.md`, which hstack does not read |

When one of these six is invoked, or when another skill tells you to follow one of them, stop before its first step. Tell the user that the skill is unavailable until hstack's Orca adapter is complete. Do not start subagents for it, do not write `~/.claude/rules/pstack-models.md`, and do not run another vendor's seat on the session model as the Claude Code adapter allows.

A skill that only cites a section of one of the six, as `no-comments` cites the Subagents section of `poteto-mode`, still runs. Read the cited section and do not start the cited skill.

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
