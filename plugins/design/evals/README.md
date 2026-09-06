# Behavioral evaluations

Each skill has an `evals/evals.json` with user prompts and observable expectations.
These scenarios are separate from manifest validation: `./scripts/validate.sh` does
not execute an agent or prove the skill's behavior.

## Run a scenario

1. Copy the scenario's raw fixture into a new temporary workspace, preserving its
   relative tree. For a Markdown scenario, create the files it describes. Keep the
   plugin's own files outside the writable test workspace.
2. Give an independent agent the scenario's `prompt`, the relevant skill entrypoint,
   and the raw workspace. Do not give it `expected_output` or `expectations` before
   execution. Load the complete plugin so its shared references are available.
3. Save the resulting artifacts and response outside this repository. Compare actual
   behavior with the expectations; inspect preserved files and runtime behavior, not
   merely whether the final answer repeats the expected wording.
4. When a browser is available, run the artifact from its final location at
   375/768/1440 pixels, exercise state transitions and keyboard behavior, and inspect
   asset/console errors. Record unavailable tooling as not run.
5. For a rerun scenario, use the result of a successful promotion, add the specified
   hand edit, then invoke the skill again. Compare contents before and after.

The variant-board fixture deliberately has different root and app design sources,
an exploration-only token mismatch, a detail control that must survive extraction,
and transitive relative CSS/SVG dependencies. It contains synthetic sample content.
Do not copy private project prototypes or research transcripts into public fixtures.

For Claude Code, a session-local `--plugin-dir <plugin-root>` load can exercise the
package without changing global installation state. Use the installed CLI's help for
available tool and permission options. For Codex, load the complete local plugin or
invoke its skill entrypoint with its sibling references accessible.

Report scenario pass/fail counts separately from checks that were not run. A source-only
evaluation cannot be reported as a successful browser test or marketplace installation.
