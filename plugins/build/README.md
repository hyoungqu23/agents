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

## Scoped corrections

`fix` addresses reported bugs and requested QA behavior/design improvements in an
existing product. It chooses the smallest complete correction, verifies supplied
claims, preserves user edits and separates applied changes from verified outcomes.
Already satisfied or refuted items can correctly result in no source changes.

```text
Use $fix to address these bugs and apply the selected QA improvements.
Preserve the existing API, selection and design tokens; verify the changed flow.
```

Claude Code supports `/build:fix`. The skill and its reference are self-contained;
no sibling helper or new state engine is installed. UI corrections need actual-app
verification; unavailable browser checks remain visible. PR replies/publication
follow the current task authorization and the relevant PR-response workflow.

Prepare independent raw tasks with `python3 scripts/behavioral/fix.py prepare --case
bug --output /tmp/new-fix-case`. The evaluation adapter is repository tooling and
does not impose a JSON schema on ordinary fix use. See
[fix evaluation setup](skills/fix/evals/SETUP.md).

## Implementation evidence

The implement [state helper](skills/implement/scripts/implementation_state.py) records
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

Structured SPEC handoffs activate the bundled original AC/question completion gate. Missing ACs, unresolved blockers, stale originals, absent semantic review and failed behavior remain gaps. Direct requirements remain supported without Product installed.

### dogfood

Use `build:dogfood` to inspect real app journeys, visuals and persistent outcomes with the available authenticated browser. It reports findings without editing app code. Coverage may be complete while issues are found. Its recorder checks local files and evidence, not the truth of visual judgment. No external QA skill is required.
