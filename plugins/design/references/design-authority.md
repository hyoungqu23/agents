# Resolve the design authority

Use this reference when creating a brief, exploring a screen, or promoting a prototype. Resolve authority from the **implementation target**, even when the prototype lives in a temporary folder or another repository.

## Find the applicable source

1. Identify the intended app, screen, and implementation path from the request and nearby code. If that choice changes which design system applies and cannot be inferred, ask for the target before changing design files.
2. Honor a design source explicitly selected by the user for this task. Otherwise walk upward from the target directory to its repository or selected project root. At each level check `DESIGN.md`, `design-system.md`, and `DESIGN_SYSTEM.md`; stop at the nearest level with a match.
3. If that level contains several candidates, follow an explicit local precedence rule or ask which one is authoritative. Do not silently merge them, prefer a filename, or combine another app's design system with this one.
4. If no design file exists, inspect applicable `AGENTS.md`/`CLAUDE.md` design rules and the target's actual styles, components, and existing HTML. Keep inline rules as a valid source; extracting them into a new file is optional.

Read the complete selected design document. Its headings need not match a template. Extract the values and rules it actually provides:

| Area | Evidence to identify |
| --- | --- |
| Product and concept | Audience, screen purpose, metaphor, what the metaphor must communicate |
| Tokens | Colors, typography, spacing, radii, shadows, motion, responsive scales |
| Components | Names, reusable elements, variants and states |
| Patterns | Navigation, hierarchy, interactions, required and prohibited treatments |
| Accessibility | Existing contrast, focus, target-size and motion requirements |
| Decisions | Chosen alternatives, reasons, exceptions and their scope |

Report absent areas as unknown or not assessed. Do not turn missing headings into defects or claim a design gate passed. The `design` plugin creates reference material; a separate review can judge it.

## Preserve existing decisions

- Existing documents keep their format, rules, and unrelated content. Default updates are targeted additions, including a Decisions Log if needed. A user-requested change to an existing value authorizes that specific edit; preserve the rest.
- Use the document's token names and values. If it specifies values but no CSS variables, introduce semantic CSS aliases in the prototype and document their mapping without rewriting the document into a new schema.
- Scope new tokens to the screen when they are not part of the shared system. Consolidate repeated **semantic roles**, not every equal numeric literal: `0`, `100%`, asset coordinates, and unrelated values that happen to match need not become global tokens.
- When no design source exists, distinguish observed implementation values from proposed choices. Create a target-local `DESIGN.md` as part of a requested brief; during exploration or promotion a local note can record extracted values until shared design documentation is requested.
- Design documents govern system tokens. The selected prototype governs structure, layout and interaction. If they disagree, identify the conflicting values and follow any explicit user decision. Otherwise preserve the selected behavior, align system values to the design source, and record the visual difference. Ask only when doing so would resolve a material design choice on the user's behalf.
- A deliberate exception records the exact property, scope, selected alternative, reason and source of that decision. A mismatch alone is not an approved exception. Do not invent a user preference or retroactively describe an agent choice as approved.

## Establish flow before visual choices

Find the applicable `flow.md` or equivalent user-flow description. Reuse it and any recorded planning review instead of restarting the planning process.

If none exists, establish the screen's entry, primary action, outcome, and relevant alternate/error paths in a compact `flow.md` beside the working prototype before building variants. Infer obvious paths from the request and existing product; ask only about choices that materially change the screen. Check that actions have destinations and required states are accounted for. This local flow check makes standalone design work possible; it does not claim that a formal planning gate ran. If the project explicitly requires a separate planning gate, honor that requirement before visual exploration.

Keep the chosen concept tied to observable states or actions. For a metaphor or motion-heavy screen, record what the metaphor communicates, when animation occurs, which data remains readable, and the reduced-motion/static alternative. Do not decorate every action with the strongest animation if the concept reserves it for a particular milestone.

## Where outputs belong

Prefer the target project's established location and ignore policy. Otherwise use a screen-local working folder for exploration and `prototype/<screen>/` for a reference. Keep private source material in its existing location; link only the evidence needed by the task. Do not alter `.gitignore`, install plugins, commit, push, or deploy merely to produce a design artifact. Carry out those actions when the user separately includes them in the requested work.
