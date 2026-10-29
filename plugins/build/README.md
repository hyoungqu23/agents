# Build

`implement` turns requirements and a selected design into working functionality in
an existing application. It preserves applicable UX patterns and user changes,
verifies actual behavior and records gaps for continuation or later review.

```text
Use $implement to implement this flow and selected prototype in apps/web.
Follow the existing filter, selection and error-handling patterns.
```

Claude Code also supports `/build:implement`. Install the plugin from this marketplace:

```text
/plugin install build --marketplace hyoungqu23/agents
```

The skill is self-contained for skill-directory installation; no product, design or
review plugin is required. It accepts existing formats and direct requirements.
Code review, Visual QA and release remain separate workflows, run when requested
or required by the project. Never interpret implementation completion as those passes.

The bundled [state helper](skills/implement/scripts/implementation_state.py) records
initial and verification source independently. It checks current-source identity,
scope, dirty-work preservation, requirement coverage and evidence references.
UI completion requires actual-app browser evidence. Missing browser access leaves
the result partial. The helper cannot prove that a claimed command ran or that the
implementation is semantically correct; actual host traces and behavioral evaluation
are required. See the [execution contract](skills/implement/references/execution-and-evidence.md).

Version 1's mechanical assessment supports Git checkouts with ordinary index state.
It requires Python 3.9+, Git and OS `O_NOFOLLOW` support (macOS/Linux). Other hosts
must disclose unavailable mechanical assessment rather than claim a computed pass.
Partial/promisor clones, submodules, conflicts and assume-unchanged/skip-worktree flags are reported rather
than silently ignored. Existing ignored dependencies/build outputs are outside the
source inventory. Do not initialize Git or change index flags to bypass a limitation.

Run the repository's validation, plugin load check and Python suite. The helper's
unit tests use synthetic evidence and do not establish model or browser behavior.
Real execution evidence and its limits are recorded in the
[forward evaluation report](../../reports/implement-evaluation-2026-10-30/README.md).
Use `python3 scripts/behavioral/implementation.py prepare --case full --output /tmp/new-case`
to prepare fresh raw inputs; it does not call a model. See [evaluation setup](skills/implement/evals/SETUP.md).
