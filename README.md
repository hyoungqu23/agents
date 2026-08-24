# HM2 Agent Tools

A cross-platform marketplace for reusable Claude Code and Codex plugins.

- Marketplace ID: `hm2-tools`
- Display name: `HM2 Agent Tools`
- Repository: `agents`

## Contents

| Plugin | Skills | Description |
| --- | --- | --- |
| [`content`](plugins/content) | `un-ai` | Content writing skills for drafting, editing, rewriting, and auditing English or Korean prose. |
| [`review`](plugins/review) | `min-hard-review` | Code review skills for pull requests, branches, diffs, and working-tree changes. |

## Repository layout

```text
.
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
└── plugins/
    ├── content/
    │   └── skills/un-ai/
    └── review/
        └── skills/min-hard-review/
```

The Claude Code and Codex manifests are platform-specific wrappers. Each skill is stored once under `plugins/<plugin>/skills/<skill>/` and shared by both.

## Local testing

### Claude Code

From the parent directory of this repository:

```text
/plugin marketplace add ./agents
/plugin install content@hm2-tools
/plugin install review@hm2-tools
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
```

The script validates JSON files, runs the installed Codex plugin validator when available, and runs Claude Code validation when the `claude` CLI is installed.

## Publishing note

Resolve the public license and third-party attribution requirements before the first public release.
