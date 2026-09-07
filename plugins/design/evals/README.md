# Behavioral evaluations

Each skill has an `evals/evals.json` with user prompts and observable expectations.
These scenarios are separate from manifest validation: `./scripts/validate.sh` does
not execute an agent or prove the skill's behavior.

## Run a scenario

1. Read the selected skill's `evals/SETUP.md` as the evaluator. Materialize the listed
   input files and perform its required prerequisites **before** launching the measured
   invocation. Every `files` entry is a regular file relative to the skill root;
   SETUP.md defines its workspace destination. Setup failures are reported separately.
2. Give an independent agent the scenario's `prompt`, the relevant skill entrypoint,
   and the raw workspace. Do not give it `expected_output` or `expectations` before
   execution. The complete plugin and its shared references must be readable, including
   inside a restricted evaluator sandbox; plugin files are not permitted output targets.
3. Save the resulting artifacts and response outside this repository. Compare actual
   behavior with the expectations; inspect preserved files and runtime behavior, not
   merely whether the final answer repeats the expected wording.
4. When a browser is available, run the artifact from its final location at
   375/768/1440 pixels, exercise state transitions and keyboard behavior, and inspect
   asset/console errors. Record unavailable tooling as not run.
5. For a rerun scenario, compare the pre-invocation baseline captured by SETUP.md with
   the result. Setup instructions belong in SETUP.md; expectations contain only results
   that can be checked after execution.

The variant-board fixture deliberately has different root and app design sources,
an exploration-only token mismatch, a detail control that must survive extraction,
and transitive relative CSS/SVG dependencies. It contains synthetic sample content.
Do not copy private project prototypes or research transcripts into public fixtures.

The module-reference fixture covers direct-file conversion and reproducible HTTP preview.
The in-app fixture has no dependencies and includes development, build, production-preview
and output-check commands. Missing-app handling is a separate scenario and cannot establish
that production isolation works.

Run the fixture and evaluation-contract checks from the repository root:

```sh
node --test plugins/design/evals/tests/fixtures.test.mjs
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

These deterministic tests check the supplied environment and setup contracts, not whether
an agent successfully follows the skills. The independent executions remain necessary.

For Claude Code, a session-local `--plugin-dir <plugin-root>` load can exercise the
package without changing global installation state. Use the installed CLI's help for
available tool and permission options. For Codex, load the complete local plugin or
invoke its skill entrypoint with its sibling references accessible.

Report scenario pass/fail counts separately from checks that were not run. A source-only
evaluation cannot be reported as a successful browser test or marketplace installation.
