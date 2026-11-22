# Changelog

## 0.2.0 - 2026-11-22

- Add seats: each pstack role runs on a Claude Code, Codex or agy seat, set in `~/.config/hstack/seats.md`. agy seats take only `gemini-*` ids without `orchestrator`, and every panel role keeps a seat from a vendor other than Claude.
- Add `scripts/hstack_seats.py`, the only way hstack starts a worker. It checks Orca, the coordinator's Orca terminal, the seat's CLI, the agy model and agy's permission rules before calling `orca orchestration worker-start`, and starts nothing when a check fails. It records each request before starting it.
- `setup-pstack` is usable again: the Orca adapter makes it write the seats file instead of `~/.claude/rules/pstack-models.md`. Five skills stay stopped until the rest of the adapter is done.

## 0.1.0 - 2026-11-21

- Import 54 pstack skills, the guide, the Claude Code adapter and the two agent definitions from `cursor/plugins` at `aaeb0ea` (pstack 0.15.46). `upstream.lock.json` records every upstream file and its hash.
- Add an Orca adapter that stops `poteto-mode`, `arena`, `interrogate`, `swarm`, `show-me-your-work` and `setup-pstack` until hstack can start workers on other vendors' models. The other 48 skills are usable.
- The adapter also maps `/pstack:` to `/hstack:` and hands the two upstream agent definitions to a general-purpose agent, because hstack does not register them.
- Leave out `make-bot-ui`, `statechart`, `create-formal-verification-skill`, `maintain-formal-verification-skill` and the guide images.
