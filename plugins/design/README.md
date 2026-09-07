# Design

Create project design briefs, compare interactive HTML layouts, and preserve a chosen prototype as an implementation reference. The same skills work in Claude Code and Codex.

| Skill | Use it when | Output |
| --- | --- | --- |
| `design-brief` | Establish or document a design system | Target-local DESIGN.md or a focused update to the existing source |
| `prototype-explore` | Compare layouts or interactions | Runnable HTML options with shareable variant URLs |
| `prototype-promote` | Keep a selected mockup as the baseline | Reference HTML, required assets, and a self-contained reference.md |

For example:

```text
Use $design-brief to document the existing design rules for apps/web.
Use $prototype-explore to compare three layouts for its activity screen.
Use $prototype-promote to preserve variant B for apps/web as prototype/activity/.
```

Claude Code also supports namespaced invocations such as `/design:prototype-promote`. Each skill can be used directly; an existing selected mockup does not need another exploration round.

## Using the result

Open the reference HTML using the mode recorded in `reference.md`: either directly as
a file, or through its documented local HTTP preview. The note also records design
decisions, intentional changes and checks that still need to be run. Use it alongside
the HTML when implementing or reviewing the screen.

Install or copy the complete plugin, including its shared `references/` folder.
For detailed behavior, see [design authority](references/design-authority.md),
[opening and verification](references/prototype-verification.md), and the
[promotion workflow](skills/prototype-promote/SKILL.md).

## Validation

Run `./scripts/validate.sh` from the repository root. Behavioral scenarios and raw fixtures are in each skill's `evals/` directory; see [the evaluation guide](evals/README.md) for exercising them in a disposable workspace.
