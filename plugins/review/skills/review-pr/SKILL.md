---
name: review-pr
description: Review a GitHub pull request end to end. Creates a dedicated worktree for the PR, delegates the review to review-code, then posts the findings the user approves as inline review comments. Use when asked to review a PR by number or URL, to post review comments to GitHub, or to continue reviewing a PR that has new commits or new replies. Do not use for uncommitted local changes; call review-code directly for those.
---

# Review PR

Orchestrate a pull request review. This skill owns worktree setup, approval, and posting. It produces no findings of its own — `review-code` is the only source of findings.

## Input

A PR number or URL. Resolve the repository from the current directory unless the URL names a different one.

## 1. Reclaim finished worktrees

Do this before creating anything, and never let it block the review.

Run `git worktree list --porcelain` and pick out worktrees whose path names a pull request (`pr-<number>-review`, or `PR-<number>-Review` from earlier conventions). For each, read its state:

```sh
gh pr view <number> --json state,title --jq '.state + "  " + .title'
```

List the `MERGED` and `CLOSED` ones with their disk size and ask which to remove. Remove only what the user confirms:

```sh
git worktree remove <path>
```

Never touch a worktree whose PR is still `OPEN` — the user may still be answering comments on it. If no worktree is finished, say nothing and move on.

## 2. Create the worktree

```sh
git worktree add ../<repo>-pr-<number>-review --detach
cd ../<repo>-pr-<number>-review && gh pr checkout <number>
```

Use `gh pr checkout` rather than fetching a branch by name — it resolves fork PRs correctly. If the worktree already exists, reuse it: fetch and fast-forward instead of recreating it.

Record the reviewed head in `.review-state.json` at the worktree root so a later run can scope itself:

```json
{ "pr": 4137, "reviewedSha": "<HEAD sha>", "answeredThreads": [] }
```

## 3. Delegate the review

Invoke `review-code` with the worktree as the working directory and the PR number as its target. Pass nothing else — it acquires its own PR context.

When `.review-state.json` already records a `reviewedSha` that is an ancestor of the new head, tell `review-code` to scope the review to `<reviewedSha>..HEAD` and to the files those commits touch. A first run reviews the whole PR.

## 4. Confirm each comment

`review-code` returns a `## PR 코멘트 추천` section: one `###` heading per comment carrying `[Px] title — path:Lnn`, with the comment text in a blockquote beneath it.

Present them as a numbered list — placement, severity, and the exact text that will be posted. Ask the user to approve all, approve a subset, edit the wording, or drop any. Post nothing until they answer. Carry edits through verbatim; do not re-polish approved text.

Also surface the `### 인라인 코멘트로 추천하지 않음` entries so the user knows what stays out of the diff, and offer to include them in the review summary body instead.

## 5. Post

Post every approved comment as a single review, never as separate comments — one review keeps the PR timeline readable and sends one notification.

Build the payload and submit it:

```sh
gh api repos/<owner>/<repo>/pulls/<number>/reviews --input review.json
```

```json
{
  "event": "COMMENT",
  "body": "<summary, or omit>",
  "comments": [
    { "path": "src/foo.ts", "line": 42, "side": "RIGHT", "body": "..." }
  ]
}
```

Use `event: "COMMENT"`. Do not use `REQUEST_CHANGES` or `APPROVE` unless the user asks for it by name — those carry review authority the user has not delegated.

If GitHub rejects a comment because its line is not in the diff, do not retry with a nearby line. Report which comment failed and leave it to the user; a mis-anchored comment is worse than a missing one.

## 6. Keep the worktree

Leave the worktree in place. The review is not over when the comments are posted — replies and new commits arrive afterward, and recreating the worktree to answer them wastes the setup. Print its path and note that a later run of this skill will offer to reclaim it once the PR closes.

## Re-running

Running this skill again on the same PR resumes rather than restarts: reuse the worktree, scope the review to commits after `reviewedSha`, and skip threads already listed in `answeredThreads`. Update both fields after posting.
