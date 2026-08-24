# HM2 Agent Tools

A cross-platform marketplace for reusable Claude Code and Codex plugins.

- Marketplace ID: `hm2-tools`
- Display name: `HM2 Agent Tools`
- Repository: `agent-tools`

## Repository layout

```text
.
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
└── plugins/
```

The Claude Code and Codex manifests are platform-specific wrappers over the same plugin sources under `plugins/`.

## Local testing

### Claude Code

From the parent directory of this repository:

```text
/plugin marketplace add ./agent-tools
```

After publishing to GitHub, replace the local path with `<github-owner>/agent-tools`.

### Codex

Add this repository as an explicit local marketplace:

```sh
codex plugin marketplace add /absolute/path/to/agent-tools
```

## Validation

Run:

```sh
./scripts/validate.sh
```

The script validates the marketplace manifests and runs Claude Code validation when the `claude` CLI is installed.
