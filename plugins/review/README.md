# Review

Code review skills for Claude Code and Codex.

## Skills

| Skill | Description |
| --- | --- |
| [`review-pr`](skills/review-pr) | Review a GitHub pull request end to end: dedicated worktree, `review-code` delegation, approval, then inline comments posted as one review. |
| [`review-code`](skills/review-code) | Completion-gated hard review for PRs, branches, diffs, and working-tree changes. Inventories every changed file, routes stack specialists, and promotes only evidence-backed findings. |
| [`review-respond`](skills/review-respond) | Answer the review on your own PR: collect the threads waiting on you, verify each claim against the code, commit fixes as new commits, then post the approved replies inside the threads with commit links. Resolves nothing unless asked. |

Each skill is stored once under `skills/<skill>/` and shared by both platform manifests.

`review-code` and `review-respond` polish PR comment text with `un-ai` from the [`content`](../content) plugin. Install both plugins for that pass; without `content`, the skills apply their comment wording rules directly and report the missing pass.
