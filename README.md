# HM2 Agent Tools

A cross-platform marketplace for reusable Claude Code and Codex plugins.

- Marketplace ID: `hm2-tools`
- Display name: `HM2 Agent Tools`
- Repository: `agents`

## Contents

| Plugin | Skills | Description |
| --- | --- | --- |
| [`content`](plugins/content) | `un-ai` | Content writing skills for drafting, editing, rewriting, and auditing English or Korean prose. |
| [`review`](plugins/review) | `review-pr`, `review-code`, `review-respond` | Code review skills for pull requests, branches, diffs, and working-tree changes. |
| [`design`](plugins/design) | `design-brief`, `prototype-explore`, `prototype-promote` | Design briefs, interactive HTML exploration, and selected prototypes preserved as implementation references. |

## Repository layout

```text
.
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
└── plugins/
    ├── content/
    │   └── skills/un-ai/
    ├── review/
    │   └── skills/{review-pr,review-code,review-respond}/
    └── design/
        ├── references/
        └── skills/{design-brief,prototype-explore,prototype-promote}/
```

The Claude Code and Codex manifests are platform-specific wrappers. Each skill is stored once under `plugins/<plugin>/skills/<skill>/` and shared by both.

## Local testing

### Claude Code

From the parent directory of this repository:

```text
/plugin marketplace add ./agents
/plugin install content@hm2-tools
/plugin install review@hm2-tools
/plugin install design@hm2-tools
```

After publishing to GitHub, replace the local path with `<github-owner>/agents`.

### Codex

Add this repository as an explicit local marketplace, then install the plugins from `HM2 Agent Tools`:

```sh
codex plugin marketplace add /absolute/path/to/agents
```

## Validation

Run:

```sh
./scripts/validate.sh
./scripts/load-check.sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
node --test plugins/design/evals/tests/fixtures.test.mjs
```

`validate.sh` validates JSON files, runs the installed Codex plugin validator when available, and runs Claude Code validation when the `claude` CLI is installed.

`load-check.sh` installs every plugin from the checkout into a scratch `CLAUDE_CONFIG_DIR` and fails unless each one reaches `enabled` with all of its skills in the loaded inventory. Manifest validation accepts a marketplace entry whose `source` path does not exist, and a skill directory whose `SKILL.md` is missing; the load check does not. It requires the `claude` CLI, touches no installed plugin of its own, and needs no network.

The Python tests cover validation-environment recovery and every skill's SKILL.md
frontmatter: delimiters that parse, a `name` matching its directory, a description that
states both when to use the skill and what to use instead, and no reference file that
nothing reaches. Neither plugin validator reads skill frontmatter. The Node tests check design
evaluation inputs, keyboard behavior, and development/production fixture isolation.
Agent-executed scenarios are described in [the design evaluation guide](plugins/design/evals/README.md).

## Publishing note

Resolve the public license and third-party attribution requirements before the first public release.
