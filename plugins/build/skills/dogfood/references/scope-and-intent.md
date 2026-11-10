# Scope and independent intent

Accept a running URL or a project whose app can be identified. Read supplied QA.md,
AC/spec/design, selected reference or PR context where relevant. A QA configuration
is optional; do not require a new document or upstream skill. Use the current user
instruction over stale QA settings, and retain existing permissions for ordinary QA
operations. Document-only/screenshot-only/code review requests do not imply dogfood.

Record a bounded charter and original required checklist before exploring. Each
expectation has its source, applicability and uncertainty. Distinguish confirmed
behavior, existing behavior under an explicit preservation requirement and a
hypothesis. Current code matching the current UI cannot establish correctness of a
requested change. Where intent is unknown, preserve the observation and question as
needs_intent; do not force either pass or a confirmed defect.

Read source/diff to choose routes, affected shared components and plausible risks.
Do not turn static suspicion into a reproduced app issue or attach arbitrary nearby
code lines. Report UI conditions and evidence without a code location when unknown.
Combine duplicate causes without dropping original journeys and affected contexts.

Optional QA.md can record URLs/API environment, allowed test organization/role,
authorized data operations and supported screen conditions. It contains no credentials,
cookies or tokens. Reading it is not authority to publish issues, fix code or deploy.
