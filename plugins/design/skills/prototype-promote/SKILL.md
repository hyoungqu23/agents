---
name: prototype-promote
description: Turn an explicitly selected HTML prototype or variant into a durable design reference with resolved tokens, working assets and interactions, and an implementation handoff. Use when the user says to keep a chosen mockup as the baseline or promote a prototype; promotion creates reference artifacts, while production implementation remains a separate task.
---

# Prototype Promote

Preserve the chosen design as a reference that a later implementation or review can use. This is a selection-and-extraction workflow, not a redesign. Read [design authority](../../references/design-authority.md) before changing files.

## 1. Resolve selection and target

Identify the source HTML/route, selected variant or explicit combination, intended app/screen, and output location. Accept selection stated in the current request or an existing user decision record. If the source has several variants and no selection, ask which one to preserve before writing the reference. A single supplied mockup explicitly requested for promotion needs no extra confirmation.

Read the whole source, relevant styles/scripts/assets, existing design source and decision notes. Record their paths and available revisions or content digests, plus the selection and date. Include the applicable design authority and transitive source dependencies in this provenance, not just the top-level HTML. Resolve design rules from the intended implementation target, not the prototype's temporary location.

Inspect existing output before writing. Compare resolved source and destination paths; do not overwrite the exploration source by accident. Prefer the project's established reference location, otherwise `prototype/<screen>/index.html` plus `reference.md`. When this collides with the source, use a separate `<screen>-reference` folder. An explicit in-place edit request authorizes targeted edits, not deleting unrelated files.

## 2. Extract the chosen design

- Copy or extract only the selected variant or the explicitly chosen combination. Preserve content, hierarchy, components, meaningful states, interactions and the selected concept.
- Remove the comparison switcher, variant routing and its global shortcuts. Remove styles, scripts and assets owned only by losing variants after tracing their consumers. Keep tabs, sliders, carousels and other controls that belong to the selected design.
- Preserve the exploration original. Rework demo logic only as needed to make the selected design function independently, with local state and simulated mutations.
- Make assets work from the destination: copy the needed local dependencies or rewrite paths correctly, including CSS imports/URLs, module imports and dynamically selected resources. Avoid dependencies on a temporary server, another worktree or an absolute home-directory path. List any intentionally retained external dependency and its offline effect.
- For source routes that require a framework, extract a portable HTML demonstration of the selected behavior. Do not copy framework components into an HTML file and call it runnable. Document any behavior that cannot be represented faithfully and keep the result draft until material choices are resolved.

## 3. Resolve tokens and differences

Use the applicable design document's system values. Replace presentation literals for reusable semantic roles with CSS custom properties; preserve explicit design exceptions. Distinguish token declarations from hardcoded usages. Do not mechanically replace literals inside images, SVG paths, unrelated scripts, percentages or all zero values.

If no design document exists, extract a local token map and mark it as derived from the chosen prototype. That does not establish an app-wide design system without a request to do so. If the user also requested a brief, write the appropriate target-local DESIGN.md using the authority rules.

Record every intentional difference from the source, including token alignment and artifact-only cleanup. Do not silently convert the selection to another concept, normalize away expressive motion, or label your own redesign as a user-approved exception. Preserve existing design documents and add only the relevant mapping or decision entries within scope.

## 4. Write the handoff

Use [the reference note shape](references/reference-note.md) for `reference.md`, adapting to an existing convention. It records:

- Source and selection evidence, target, output paths and how to open the artifact.
- Applicable design authority and token mapping, including screen-local additions.
- Required components, content, states, transitions, motion and static/reduced-motion behavior.
- Intentional differences with their reasons and decision sources.
- Asset dependencies, checks actually run, remaining limitations and implementation notes.

Keep paths relative to the project or artifact where possible. Label proposals and unknowns. The handoff must stand on its own for a new session; a chat link alone is not the design specification. It is a design reference, not evidence that production code was implemented, tested or approved.

## 5. Verify and finish

Follow [prototype verification](../../references/prototype-verification.md) from the final location. Fix known broken assets, layout or interactions before calling the artifact ready. If tools are unavailable, deliver the explicit verification limits and manual checks; never invent screenshots or passing tests.

On a rerun, resolve the current design authority again and compare it, all relevant source dependencies, the selection/target, and the existing reference against the recorded provenance. Return existing artifacts unchanged only when those inputs and requested scope are unchanged; do not duplicate decisions or rewrite files just to refresh a date. Missing revision evidence requires inspecting the current inputs, not assuming a no-op. If anything changed, compare the source, reference, design rules and recorded differences; preserve hand edits. Update only what the new request authorizes and ask if a conflict would discard a meaningful choice. Record changed input revisions and intentional differences, then rerun affected checks.

Return the reference HTML and note paths, the selected design, intentional differences, and verification results. Implementing production code, replacing the main app, committing or publishing requires that work to be included in the user's request.
