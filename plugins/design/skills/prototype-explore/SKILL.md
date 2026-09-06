---
name: prototype-explore
description: Explore structurally different UI options in an interactive HTML prototype with shareable variant URLs. Use when comparing screen layouts or interactions before selecting a design. For an already selected design that should become an implementation reference, use prototype-promote instead.
---

# Prototype Explore

Build a runnable comparison that answers a specific design question. Read [design authority](../../references/design-authority.md), resolve the target's design source, and establish the applicable flow before drawing variants.

## Choose the shape

State the question and the structural alternatives. Default to three variants and cap at five unless the user explicitly requests another number. Vary hierarchy, layout or the primary interaction, not just colors and copy. Respect a selected concept and established tokens while exploring alternatives within them.

Use the existing screen's shell and content when they provide useful context. Default to a portable HTML working prototype that reproduces that context. If the user requests an in-app route, follow the app's conventions and keep experimentation out of its production build. Do not edit a production screen merely because it resembles the prototype.

Use available real content or clearly labeled sample content. Do not invent user research, product claims or lorem ipsum. Keep state in memory and simulate mutations locally. The comparison must not submit forms, call live mutation endpoints, or change production data.

## Make comparison easy

- Use `?variant=A`, `?variant=B`, and so on, with a stable default and graceful fallback for an unknown key. Each URL opens the corresponding variant on reload.
- Provide a visually distinct bottom switcher with previous/next controls and a descriptive variant label. Keep it clear of content and focus targets.
- Update URL and rendered state together. If using browser history, handle back/forward navigation consistently.
- Arrow keys may switch variants only when focus is outside editable controls and widgets that own those keys. Do not break inputs, selects, radio groups, sliders, tabs or carousels.
- Preserve useful state or provide a clear reset when switching. Share content and low-level tokens when helpful, but keep each layout free to differ.
- In an app, gate both experiment routing and controls so the normal production path stays intact. A standalone file should identify itself as an exploration artifact and remain outside production entrypoints.

Keep styles and demonstration scripts readable enough to extract the selected design later. Preserve relative assets or list dependencies needed to run the prototype. One file is preferable when it is practical, not a reason to inline large assets or discard required behavior.

## Verify and hand over

Follow [prototype verification](../../references/prototype-verification.md). Fix observed failures within the prototype and record unrun checks honestly. Iterate with targeted edits when feedback arrives.

Return the runnable path or URL, variant keys and structural differences, the question each option tests, and verification limits. Record the user's selected variant or explicit combination and their stated reason when supplied. A currently visible variant, a default URL, or silence is not a selection.

Keep exploration material intact. Once the user chooses a design, `prototype-promote` can create a separate reference from it; exploration does not automatically update production code or declare a winner.
