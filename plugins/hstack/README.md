# Hstack

> **Not usable yet: `poteto-mode`, `arena`, `interrogate`, `swarm`, `show-me-your-work`, `setup-pstack`.** The first five need workers or reviewers on other vendors' models, and hstack cannot start those until its Orca adapter is complete. `setup-pstack` writes model choices hstack does not read. Each one stops and says so when invoked. The other 48 skills work now.

Hstack is [pstack](https://github.com/cursor/plugins/tree/main/pstack) for Claude Code, imported with its source text intact. pstack is written by Lauren Tan and published under the MIT license; see [LICENSE](LICENSE) and the original [README](UPSTREAM-README.md).

Hstack is for Claude Code only. Install it from this marketplace and call a skill with the plugin prefix:

```text
/plugin install hstack@hm2-tools
/hstack:how
```

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

## Not imported

| Upstream | Why |
| --- | --- |
| `skills/make-bot-ui` | It drives Cursor Automations, which Claude Code does not have |
| `skills/statechart`, `skills/create-formal-verification-skill`, `skills/maintain-formal-verification-skill` | They need the TLA+ model checker. The three refer to each other and will be imported together |
| `docs/guide/images/` | Six illustrations, 2.2 MB. The guide reads without them |
| `plugin.json`, `.claude-plugin/` | The upstream manifests name the plugin `pstack` |

`poteto-help` still lists the four skipped skills. Invoking one reports that the skill does not exist.

## Updating

```sh
python3 scripts/import_upstream.py sync --plugin plugins/hstack --source <checkout of cursor/plugins>
python3 scripts/import_upstream.py check --plugin plugins/hstack --source <the same checkout>
```

`sync` rewrites the imported files from the checkout and inserts the generated line again. It reports upstream files the lock does not classify instead of importing them. Do not edit an imported file by hand: `check` fails when a file differs from the hash in the lock.
