---
name: hstack
description: "Start work in poteto-mode with hstack's seats, where reviews and second opinions come from Codex or agy workers run by Orca. Use when the user types /hstack:hstack or asks to work in hstack. Do not use to change the seats, which is setup-pstack, or for a single principle or helper skill the user named."
disable-model-invocation: true
---

# hstack

hstack is pstack for Claude Code, with other vendors' seats run as Orca workers.

1. Read [the Claude Code adapter](../../docs/harness/claude-code.md), then [the Orca adapter](../../docs/harness/orca.md). The Orca adapter wins where the two disagree.
2. Run `python3 <hstack>/scripts/hstack_seats.py validate --offline`, with `<hstack>` the folder two levels above this file. It checks the seats file only. When it fails, show what it printed, tell the user to run `/hstack:setup-pstack`, and stop.
3. Read [poteto-mode](../poteto-mode/SKILL.md) and follow it with the user's request. Once a playbook is matched, check the workers it will start as the Orca adapter's "Before the first step" says.

When the matched playbook is Autonomous run, Autopilot-full, Autopilot-stack, Babysit or Shipping, tell the user once that hstack has not yet checked that playbook with Orca workers, then follow it.
