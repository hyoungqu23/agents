# PR context

Repository: acme/billing-web. PR #91 "Add archived badge", authored by the current user (`hm2`), head branch `feat/archived-badge`, `viewerDidAuthor` true, `reviewDecision` is `APPROVED`. The current checkout is on `main`, not on the PR branch. A worktree `../billing-web-pr-91-review` exists from an earlier reviewer run.

# State file already present

`$(git rev-parse --git-dir)/review-respond/91.json`:

```json
{
  "pr": 91,
  "repo": "acme/billing-web",
  "headSha": "b7d2e10",
  "handled": [
    { "thread": "PRRT_A1", "lastComment": "PRRC_a1", "class": "fix", "commit": "b7d2e10", "repliedAt": "2026-09-07T09:12:00Z" }
  ],
  "conversation": []
}
```

# Review snapshot

```json
[
  { "id": "PRRT_A1", "path": "src/ui/Badge.tsx", "line": 8, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [
      { "id": "PRRC_a1", "author": "dana", "body": "aria-label이 빠졌습니다." },
      { "id": "PRRC_a2", "author": "hm2", "body": "aria-label 추가. b7d2e10 <!-- review-respond -->" }
    ] },
  { "id": "PRRT_A2", "path": "src/ui/Badge.tsx", "line": 15, "isResolved": false, "isOutdated": false, "viewerCanResolve": true,
    "comments": [
      { "id": "PRRC_b1", "author": "dana", "body": "nitpick (non-blocking): 색상 토큰은 `--badge-muted`를 쓰는 편이 디자인 문서와 맞습니다." }
    ] }
]
```

`reviews` shows `APPROVED` by dana after PRRC_a2. No conversation comments.
