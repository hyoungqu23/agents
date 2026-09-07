# Reference note

Use a short Markdown note next to the promoted artifact. The following is a content guide, not a rigid parser schema. Omit irrelevant sections, preserve an existing project format, and replace the example fields with actual evidence.

```markdown
# <Screen> design reference

Status: reference | draft
Date: <date of this revision>
Target: <app/screen and intended implementation path>
Artifact: <relative path to HTML>
Source: <source path or URL, variant/combination and available commit or digest>
Input revisions: <source HTML, relevant transitive dependencies and design-authority revisions/digests>
Selection: <what the user selected and where that decision was recorded>
Design authority: <applicable document or inline rules; otherwise derived local tokens>
Verification: <verified scope, or source-only with browser checks not run>

## Open the reference
<Opening mode: direct file or HTTP preview. File to open, or preview command with working directory, runtime and URL. Distinguish a verified command from a suggested but unrun command.>

## Design to preserve
<Purpose, concept, hierarchy, components, important content and responsive behavior.>

| State / action | Visible result | Transition / reset | Implementation note |
| --- | --- | --- | --- |
| <state or action> | <what changes> | <next state or replay> | <demo vs actual behavior> |

## Tokens
| Role | CSS property / value | Authority / scope |
| --- | --- | --- |
| <semantic role> | <custom property and value> | <source or prototype-local choice> |

## Intentional differences
| Source behavior / value | Reference behavior / value | Reason and decision source |
| --- | --- | --- |
| <specific difference> | <result> | <user choice, design rule, or artifact cleanup> |

## Motion and accessibility
<Keyboard/focus behavior, readable data, animation trigger and reduced-motion/static state.>

## Assets and dependencies
<Relative paths, external dependencies and offline limitations.>

## Verification and remaining work
<Actual viewport, interaction, asset and comparison checks, evidence paths, failures or unrun checks.>
<Production work still required; unresolved design choices remain explicit.>
```

`reference` means the chosen design has been captured, not that every browser check passed. State verification coverage separately. Known material breakage or unresolved selection remains `draft`.

Do not leave the template's angle-bracket examples in a delivered note. Do not require empty tables or invent a reason when the user only selected an option; the selection itself is sufficient evidence.
