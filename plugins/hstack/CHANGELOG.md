# Changelog

## 0.1.0 - 2026-11-21

- Import 54 pstack skills, the guide, the Claude Code adapter and the two agent definitions from `cursor/plugins` at `aaeb0ea` (pstack 0.15.46). `upstream.lock.json` records every upstream file and its hash.
- Add an Orca adapter that stops `poteto-mode`, `arena`, `interrogate`, `swarm`, `show-me-your-work` and `setup-pstack` until hstack can start workers on other vendors' models. The other 48 skills are usable.
- The adapter also maps `/pstack:` to `/hstack:` and hands the two upstream agent definitions to a general-purpose agent, because hstack does not register them.
- Leave out `make-bot-ui`, `statechart`, `create-formal-verification-skill`, `maintain-formal-verification-skill` and the guide images.
