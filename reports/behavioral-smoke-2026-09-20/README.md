# Behavioral smoke result — 2026-09-20

Real executor: `gpt-5.6-sol`, low reasoning, Codex CLI 0.153.4.
All 3 scenarios passed all 15 deterministic checks in about 131 seconds.
The primary agent also read the generated artifacts and review command trace:

- Design: app-local document updated; original colors, component and motion rules preserved.
- Content: requested intro removed; dates, counts, uncertainty and tentative schedule preserved; no added cause or promise observed.
- Review: identified the unsafe cast at `src/api/toInvoice.ts:9`, traced the missing archived label, proposed a domain/consumer fix, and did not claim to run tests.

This archive includes exact tasks, source/output hashes, individual results and generated artifacts.
The full source snapshots and event logs remain at `/private/tmp/hm2-behavioral-approved-20260920`.
`summary.json` records the base commit and dirty working tree; this is evidence for the local patch,
not for a new committed revision or a hosted GitHub Actions run.

Limits: 3 smoke scenarios, not the full behavioral suite. Local Codex also loaded global skill metadata
and warned that some skill descriptions were shortened; each task nevertheless read its explicit
copied SKILL.md and local references. A clean CI run is still required for release evidence.
No GitHub secret, branch protection, release policy or remote workflow was changed or executed.
