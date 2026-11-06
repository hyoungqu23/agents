# HM2 Review Harness

A local service that queues the four review workflows, validates source evidence,
and prepares unsubmitted GitHub Pending drafts. It never changes application source,
submits reviews, approves PRs, publishes immediate replies or resolves threads.

## Install on another Mac

The release package contains its matching review instructions, shared references,
and trusted validation/draft helpers. No developer checkout or agent skill cache is
needed after installation. Python 3.12+ is supported; the Homebrew formula manages
its declared Python. Authenticate `gh` and the selected `codex` or `claude` CLI.

Before the first release, preview installation can use the package subdirectory:

```sh
uv tool install 'git+https://github.com/hyoungqu23/agents.git@codex/review-harness-runtime#subdirectory=tools/review-harness'
```

This branch is a preview, not a stable release. After a reviewed release and its
generated formula PR are published, the repository also acts as an explicit tap:

```sh
brew tap hyoungqu23/agents https://github.com/hyoungqu23/agents.git
brew install hyoungqu23/agents/hm2-review-harness
hm2-review-harness setup --repo owner/application --path /absolute/application --provider codex
hm2-review-harness doctor
brew services start hm2-review-harness
```

The formula does not exist on main until the first release's formula PR is merged.
Do not advertise `brew install` as already available before that step. Private
repositories/assets require their own authenticated download validation.

`setup` records installed executable paths and verifies the configured GitHub account
and tool-disabled CLI capabilities. `doctor` does not establish model quality or live
Pending API compatibility. Agent subscriptions/API credentials remain device-local;
no GitHub token or unrelated cloud credential is passed to the model process.

## Enable automatic drafts

Installation defaults to local reports. To authorize Pending creation and additions
in the configured repository scope, stop overlapping writers on other devices and run:

```sh
hm2-review-harness setup --pending --single-writer
```

No per-comment approval is requested within this scope. Same-account Pending drafts
remain private until you submit them yourself in GitHub. Existing text/deletions,
manual drafts and older-head Pending reviews are protected. Their conflicts remain
local; the service keeps analyzing new revisions. Immediate comments are never a fallback.
Use `disable-pending` to return to local-only operation.

Queued scope and current authorization are checked again before delivery and every
API mutation. Pausing, disabling drafts or removing a repository also blocks an
in-flight review's later writes. A locally blocked, unsent operation is recorded as
such, so re-enabling permission does not confuse it with an uncertain network write.
Distinct new defects may share a line with old claims; deduplication uses recorded
finding identities rather than discarding everything at that source line.

## Four workflows

| Workflow | Trigger and behavior |
| --- | --- |
| S1 self review | The configured build `implement` assessment completes with `--notify-review`; capture staged/unstaged/untracked source in a separate equivalent snapshot and run review-code. Requires build plugin 0.3.0+ and a registered checkout path. |
| S2 author response | An own PR receives new inline/review-body/conversation input; verify every claim, prepare fixes as proposals and responses as drafts. Only inline responses support GitHub Pending delivery. |
| S3 reviewer | A person/team requests review, or `enqueue-pr` explicitly selects it; inspect the pinned PR and save supported comments as Pending. |
| S4 re-review | A tracked, previously reviewed PR changes; reassess the original claims and inspect the previous-review delta and current code scope independently. Unavailable previous objects remain a gap. |

An `implement` event only queues work; it does not start/install the service. Old
build plugins can explicitly use `notify-implementation --worktree PATH --assessment FILE`
with a complete trusted assessment, but this fallback is not automatic S1 integration.

P1/P2/P3/P999/질문 are the only generated prefixes. P999 is optional style/taste;
questions have no severity. Existing findings retain their IDs and original priority
when fixed. A proposed fix never gets a completion reply before current-source proof.

## Inspect and control

```sh
hm2-review-harness inbox
hm2-review-harness show JOB_PREFIX
hm2-review-harness enqueue-pr --repo owner/application --pr 123
hm2-review-harness run-once
hm2-review-harness pause
hm2-review-harness resume
```

`run-once` polls and processes at most one queued job. `serve` maintains the queue;
notifications and logs only report a job state change. Input is checked again before
Pending delivery, including same-head conversation edits. Submitted rounds retain
receipts and a new round gets a fresh Pending. Uncertain writes are not blindly retried.

Runs distinguish complete/partial/invalid analysis from local/Pending persistence.
Text packets are bounded (default 1 MB); omitted/binary paths and inaccessible
contracts remain partial. Reviewers receive immutable source as data with command,
connector/plugin and network tools disabled. They do not execute tests or target
scripts. Static quote/coverage checks cannot certify the model's reasoning.
Codex adapter flags are capability-checked against the installed CLI; see
[noninteractive mode](https://developers.openai.com/codex/noninteractive) and
[configuration reference](https://developers.openai.com/codex/config-reference).

State lives in `~/Library/Application Support/hm2-review-harness/` or an explicit
`--state-home`/`HM2_REVIEW_HOME`. Configuration limits polling, per-run duration and
daily model calls. Unfinished reviews, authentication failures, budgets, draft
conflicts and uncertain writes remain visible in the inbox. A single local lock
does not coordinate other Macs; the first version supports one writer per account
and overlapping repository scope, not distributed exactly-once processing.

Use `reconcile JOB_PREFIX` for read-only journal recovery after an uncertain write.
Only positive reconciliation enables a later explicit `retry JOB_PREFIX`; missing,
edited or ambiguous remote content remains protected. Reports retain both analysis
and actual delivery failures, including candidates kept local to avoid reposting a
published concern. Your own submitted review does not trigger another review loop.

## Update, move and remove

```sh
brew services stop hm2-review-harness
brew upgrade hyoungqu23/agents/hm2-review-harness
hm2-review-harness doctor
brew services start hm2-review-harness
```

Keep a state backup before upgrades. Unsupported DB versions fail closed; a package
downgrade is not a DB downgrade. Reconcile remote receipts after restoring state.

`export settings.json` excludes credentials and machine paths; `--include-history`
additionally exports completed PR assessments and draft receipts, not source or model
logs. On a new Mac use `import settings.json`, then `setup` to authenticate/map paths
and `resume`. Imports are paused with Pending writes disabled. Stop the previous
writer before explicitly enabling the new one. Settings/history are not cloud-synced.

To remove, stop the service then `brew uninstall hm2-review-harness`. Settings and
review history are retained for reinstall; deleting that user-data folder is a
separate explicit action. No application checkout or user-owned worktree is removed.

`retention_days` defaults to 14: the service prunes aged superseded/closed-PR runs
and aged S1 runs, keeping claim history and receipts. Open PRs and uncertain writes
are protected. `prune --days 14` previews eligible owned runs; stop the service and
add `--apply` for manual cleanup. A 2 GiB pre-job state-budget check pauses new work
as `storage_limited`; this is a cooperative check, not an OS filesystem quota.

## Build and release

```sh
uv build tools/review-harness --out-dir /tmp/hm2-review-dist
python3 tools/review-harness/packaging/make_formula.py --repo hyoungqu23/agents \
  --tag review-harness-v0.1.0 --sdist /tmp/hm2-review-dist/hm2_review_harness-0.1.0.tar.gz \
  --wheel /tmp/hm2-review-dist/hm2_review_harness-0.1.0-py3-none-any.whl \
  --output /tmp/Formula/hm2-review-harness.rb
```

The build copies the canonical review/content sources once into a checksummed
release bundle; generated copies are not maintained by hand. The sdist also carries
that bundle and can build a wheel outside this monorepo. The release workflow builds
and tests artifacts on Linux/macOS, uploads wheel/sdist/checksums/formula, and can
open a formula-update PR. Publishing requires a trusted tag and the repository's
release-enable setting; public licensing/attribution must be resolved per root README.
No release, tap registration or launchd installation happens merely by merging code.
