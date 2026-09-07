# Changelog

## 0.3.0 - 2026-09-08

- Add the `review-respond` skill for answering reviews on pull requests you authored: verify each claim, commit fixes as new commits, reply inside the threads, resolve nothing unless asked.
- Define `review-pr`'s `answeredThreads` entries as GraphQL thread node IDs and mark its worktree as reviewer-only.

## 0.2.1 - 2026-09-07

- Route PR comment wording to `un-ai` from the `content` plugin instead of external writing skills.
- Describe primary-source contract lookup directly instead of routing to an external research skill.
- Remove external source attributions from the review lenses.

## 0.2.0 - 2026-08-24

- Add the `review-pr` skill.

## 0.1.0 - 2026-08-24

- Add the `review-code` skill.
- Add Claude Code and Codex plugin manifests.
