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

## Promotion behavior

Promotion creates a design reference for later implementation and review. It keeps the selected layout, states and interactions; aligns system tokens with the applicable design source; removes comparison-only controls; and records intentional differences. It preserves the exploration original and existing reference edits on reruns.

The nearest design document is resolved from the intended app or screen, not from a temporary prototype folder. Existing document formats and inline project rules remain valid. Tokens come from the applicable design source; structure and interaction come from the selected prototype. Material conflicts are surfaced with their evidence.

Browser verification checks assets, responsive layouts at 375/768/1440 pixels, keyboard behavior, state transitions and reduced motion when tools are available. The note distinguishes actual checks from unverified behavior. A missing browser does not produce a fabricated pass.

## Packaging

Shared authority and verification guidance lives in `references/` at the plugin root. Individual skills link to it with plugin-relative paths, so install or copy the complete plugin when using these skills. No gstack binary, Pretext runtime, Figma service, `product` plugin, or specific browser tool is required.

The plugin creates design evidence. It does not implement a separate product planning or design approval gate. It can consume an existing flow and planning review, or establish a compact local flow for standalone exploration.

## Validation

Run `./scripts/validate.sh` from the repository root. Behavioral scenarios and raw fixtures are in each skill's `evals/` directory; see [the evaluation guide](evals/README.md) for exercising them in a disposable workspace.

## Design references

The workflow is informed by [mattpocock's prototype skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/prototype) for structural variation and [gstack's design-html skill](https://github.com/garrytan/gstack/tree/main/design-html) for design-token authority and viewport verification. These are references, not runtime dependencies. HM2's promotion workflow preserves a separate reference artifact and handoff after selection.
