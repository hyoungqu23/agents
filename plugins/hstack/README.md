# Hstack

> **Not usable yet: `arena`, `interrogate`, `swarm`.** They start panels of workers on several vendors' models, and hstack has not adapted them yet. Each one stops and says so when invoked, and a step that routes to one of them is skipped with a line, or stops the playbook when a later step needs its output. The other 52 skills work now.

Hstack is [pstack](https://github.com/cursor/plugins/tree/main/pstack) for Claude Code, imported with its source text intact. pstack is written by Lauren Tan and published under the MIT license; see [LICENSE](LICENSE) and the original [README](UPSTREAM-README.md).

Hstack is for Claude Code only. Install it from this marketplace and call a skill with the plugin prefix:

```text
/plugin install hstack@hm2-tools
/hstack:how
```

Start work with `/hstack:hstack <goal>`. It checks your seats, then follows `poteto-mode`. Reviews and second opinions from another vendor run as Orca workers, so start Claude Code in an Orca terminal.

Installing the `skills/` folder by itself is not supported. The skills link `docs/` in the plugin folder, and their short names (`how`, `why`, `tdd`) would be installed without a prefix.

## What is imported

Files come from `harness/pstack/claude-code/` in `cursor/plugins`, the Claude Code bundle that repository generates from pstack. [`upstream.lock.json`](upstream.lock.json) records the commit, every upstream file, and what was done with it.

| Status | Meaning |
| --- | --- |
| `verbatim` | Byte-for-byte the upstream file |
| `injected` | The upstream file plus one generated line that points at [the Orca adapter](docs/harness/orca.md) |
| `skipped` | Not imported |
| `local` | Written in this repository |

Two things are placed differently from upstream. `agents/` is imported as `upstream-agents/`, so Claude Code does not register the two definitions as agents. The upstream `README.md` is imported as `UPSTREAM-README.md`, because this file takes its place.

To read a file as upstream has it, open `https://github.com/cursor/plugins/blob/<commit>/<upstream path>` with the commit and path from the lock, or replace the commit with `main` for the latest text.

## Seats

Each pstack role runs on a seat: Claude Code, Codex or agy, with a model. `/hstack:setup-pstack` writes your choices to `~/.config/hstack/seats.md`; roles you leave out keep the defaults. [`scripts/hstack_seats.py`](scripts/hstack_seats.py) reads that file, and it is the only way hstack starts a worker. Before each start it checks that Orca is reachable, that this session runs in an Orca terminal, that the seat's CLI is installed, that an agy model is one `agy models` offers, and that agy may report and read without asking. When a check fails it starts nothing. It writes each request to a run record under `~/.local/state/hm2/hstack/runs/` before starting, so a lost response can be looked up instead of starting the worker twice.

## Not imported

| Upstream | Why |
| --- | --- |
| `skills/make-bot-ui` | It drives Cursor Automations, which Claude Code does not have |
| `skills/statechart`, `skills/create-formal-verification-skill`, `skills/maintain-formal-verification-skill` | They need the TLA+ model checker. The three refer to each other and will be imported together |
| `docs/guide/images/` | Six illustrations, 2.2 MB. The guide reads without them |
| `plugin.json`, `.claude-plugin/` | The upstream manifests name the plugin `pstack` |

`poteto-help` still lists the four skipped skills. Invoking one reports that the skill does not exist.

## Updating

Every Monday the `hstack-upstream-sync` workflow compares `cursor/plugins` `main` with the commit in the lock. When pstack changed, it opens a pull request that re-imports the files, bumps this plugin's patch version and lists what needs a decision. It never merges. While that pull request is open, later runs leave it as it is and add a comment when pstack has changed beyond what it covers.

The pull request is opened by the workflow token, so its `validate` run waits for approval. Approve it first. `validate` then compares the lock with the upstream commit itself, which is what catches an upstream file the lock does not mention.

To do the same by hand:

```sh
python3 scripts/import_upstream.py sync --plugin plugins/hstack --source <checkout of cursor/plugins>
python3 scripts/import_upstream.py check --plugin plugins/hstack --source <the same checkout>
```

`sync` reads the checkout's `HEAD` commit, rewrites the imported files and inserts the generated line again. It reports upstream files the lock does not classify instead of importing them. To classify the files a sync pull request lists, first check the upstream checkout out at the commit in that pull request's lock, or files added upstream since then come in as well. To leave some out, add their paths to `skip` in the lock first, then run `sync --accept-new` once for the rest. In the other order the files meant to be left out are imported too.

A file deleted upstream is reported and kept. Delete the file together with its entry in the lock, or keep it by removing `upstream`, `upstream_blob` and `applied_blob` from the entry and setting its `status` to `local`.

Do not edit an imported file by hand without recording it: `check` fails when a file differs from the hash in the lock. When an upstream skill has to change to run here, edit it and record the patch:

```sh
python3 scripts/import_upstream.py patch --plugin plugins/hstack --path skills/<name>/SKILL.md
```

From then on `sync` merges upstream changes into that file instead of replacing it. A change it cannot merge is left with conflict markers, and `check` fails until they are resolved and the file is recorded with `patch` again. `sync` writes nothing when any patched file differs from what was recorded, so an edit made after `patch` has to be recorded or undone first.
