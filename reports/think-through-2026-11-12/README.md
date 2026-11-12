# Think Through behavioral evaluation

The eight scenarios in `plugins/learn/skills/think-through/evals/evals.json` and a
five-turn resumed conversation passed on 2026-11-12. [results.json](results.json)
retains every learner request, actual response and qualitative assessment, plus
source hashes linking the tested instructions to this change.

Each isolated scenario ran once through `codex exec --ignore-user-config
--ephemeral --sandbox workspace-write --json`, with web search disabled and no
model or reasoning override. The executor received copies of the Learn skills
without `evals/`, a skill inventory with actual entrypoint paths and the learner
request. Expectations stayed outside the executor workspace. The conversation
used one persisted thread and four `codex exec resume` calls. Its five session
metadata records identify `gpt-6.1-sol`; the ephemeral scenario events do not
identify their resolved model.

All 13 turns completed successfully without changing the executor workspaces.
The parent inspected the actual responses against the expectations. This is a
single-run qualitative check, not an automated semantic CI gate, a cross-model
benchmark or proof of long-term learning. Native plugin loading was checked
separately with `scripts/load-check.sh`.
