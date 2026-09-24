# HM2 Agent Tools

A cross-platform marketplace for reusable Claude Code and Codex plugins.

- Marketplace ID: `hm2-tools`
- Display name: `HM2 Agent Tools`
- Repository: `agents`

## Contents

| Plugin | Skills | Description |
| --- | --- | --- |
| [`content`](plugins/content) | `un-ai` | Content writing skills for drafting, editing, rewriting, and auditing English or Korean prose. |
| [`review`](plugins/review) | `review-pr`, `review-code`, `review-respond`, `review-check` | Code review, read-only review claim verification, and pull request responses. |
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
    │   └── skills/{review-pr,review-code,review-respond,review-check}/
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

`validate.sh` validates JSON files and requires the official Codex plugin validator.
It defaults to the installed plugin-creator validator under `~/.codex`; set
`CODEX_PLUGIN_VALIDATOR` to use another official checkout. A missing validator is
a failure, never a successful skip. CI checks out OpenAI's validator at commit
`5c5308fc9a9ee789049d646ef11e5400384b9c6f` with its sibling imports and installs
PyYAML explicitly. Claude Code validation runs when the `claude` CLI is installed;
CI installs it and also requires the load check below.

`load-check.sh` installs every plugin from the checkout into a scratch `CLAUDE_CONFIG_DIR` and fails unless each one reaches `enabled` with all of its skills in the loaded inventory. Manifest validation accepts a marketplace entry whose `source` path does not exist, and a skill directory whose `SKILL.md` is missing; the load check does not. It requires the `claude` CLI, touches no installed plugin of its own, and needs no network.

The Python tests cover validation-environment recovery and every skill's SKILL.md
frontmatter: delimiters that parse, a `name` matching its directory, a description that
states both when to use the skill and what to use instead, and no reference file that
nothing reaches. These repository-specific routing and reachability checks supplement
the platform validators. The Node tests check design
evaluation inputs, keyboard behavior, and development/production fixture isolation.
Agent-executed scenarios are described in [the design evaluation guide](plugins/design/evals/README.md).

### Behavioral smoke checks

Structural tests do not establish that an agent follows a skill. Run actual Codex
invocations separately, using a logged-in CLI or `CODEX_API_KEY`:

```sh
python3 scripts/behavioral/run.py --model <model-id> --output /tmp/hm2-behavioral-unique-run
```

This uses model capacity and sends the selected plugin instructions, references and
synthetic fixtures to OpenAI. It runs four scenarios in disposable workspaces and
checks real artifacts for design-rule preservation, editing fidelity, and a known
cross-file review defect. Failures, timeouts and missing outputs return nonzero;
the output directory retains prompts, traces, snapshots and individual checks.

The separate **behavioral-smoke** workflow runs on explicit dispatch against reviewed
`main`, requires the `CODEX_API_KEY` repository secret and a model ID, and uploads
evidence even on scenario failure. It deliberately does not run credentialed agents
against fork PR code. Before release, require a successful run for the release commit
and inspect its artifacts; the ordinary `validate` job is not a behavioral pass.
Branch protection/release policy must enforce that requirement if publishing is
automated. See [the behavioral runner guide](scripts/behavioral/README.md) for scope
and the remaining human evaluation requirements.

## Publishing note

Resolve the public license and third-party attribution requirements before the first public release.
