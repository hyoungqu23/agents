# Hosts: install, invoke, switch

The learning folder is the only shared state. Any supported host can continue
any folder; no conversation ID, chat log or login is stored in it.

## Install

Both hosts install the `learn` plugin from the `hm2-tools` marketplace (this
repository). Each skill exists once under `plugins/learn/skills/study-loop/`.

| Host | Install | Invoke |
| --- | --- | --- |
| Claude Code CLI or desktop | `/plugin marketplace add <path-or-owner/repo>` then `/plugin install learn@hm2-tools` | `/learn:study-loop` |
| Codex CLI | `codex plugin marketplace add <absolute path>` then install `learn` from HM2 Agent Tools | `$study-loop` |

The plugin skill is namespaced, so it does not replace other `learn` or `tutor`
skills. Installing or updating never touches learning folders.

## Requirements

- Python 3.10+ found as `python3`, `python3.13`, `python3.12`, `python3.11` or
  `python3.10` (see SKILL.md). The engine refuses older Python with
  `RUNTIME_UNSUPPORTED` rather than misbehaving.
- Permission to run that Python and to write the learning folder. A host that
  can read files but cannot run the script cannot use this skill.
- A local file system. Cloud-synced folders written from two machines at once
  are not supported.

## Switch hosts

1. In the first host, pause (`session.pause` with the learner's words), or leave
   a question pending.
2. In the other host, open the same folder path, query `view=resume`, and act on
   `nextAction`. A paused session needs `session.resume` with the learner's words.
3. Set `actor.host` to the host you are running in. The record keeps which host
   made each write.

Run one host at a time on a folder. A second writer waits on the lock and then
gets `LOCK_BUSY`; never delete `records/.lock`.

## Cowork and cloud sessions

Cowork and cloud sessions load skills from the claude.ai account, not from the
local plugin, and may run in the cloud with local files reached through the
desktop app. Treat them as unverified until a run there can execute this
skill's Python script against the same folder.
