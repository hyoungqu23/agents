---
name: design-brief
description: Create or update a project's DESIGN.md from existing design rules, code, HTML, and a product brief. Use when establishing reusable visual, interaction, and concept decisions before prototyping, or documenting an existing design system. Preserve the nearest existing design source and its format.
---

# Design Brief

Make a concise design reference that another designer or coding agent can use without rediscovering the product's choices. Read [design authority](../../references/design-authority.md) before locating or editing the applicable source.

## Establish the brief

Identify the target app/screen, audience, primary outcome, available content, selected concept, and supplied references. Read existing components and styles to separate the current system from proposed changes. Reuse decisions already made in the conversation; bundle only questions that materially affect the result.

For an existing system, report what can be recovered and add only missing information requested or necessary for the brief. For a new system, make a small coherent proposal based on the product and identify consequential choices still awaiting selection. Do not invent research, approval, business facts, or a settled brand direction.

## Write the reference

Use the existing design document's organization. For a new target-local `DESIGN.md`, include the areas the task needs:

- Product purpose, audience, screen scope and available content.
- Concept and visual direction, including what the metaphor or motion communicates.
- Semantic tokens: typography, colors, spacing, radii, shadows and motion. Record concrete values and reuse existing CSS names where present.
- Layout, responsive behavior, components and their relevant states.
- Interaction, accessibility and reduced-motion/static behavior.
- Decisions Log: decision, scope, reason, source, date, and whether it is observed, proposed or explicitly selected.

Include source paths so a later implementation can find the actual CSS, components or HTML. Reference local tokens rather than duplicating an entire library. Where the source lacks a rule, say so instead of filling every section with generic defaults.

A brief can be produced directly from an existing HTML prototype. Extract its design decisions without treating all incidental measurements as shared tokens or all existing behavior as intentional. Preserve nonvisual rules in an existing DESIGN.md, such as component architecture or naming conventions.

## Finish

Re-read the result against the original sources. Check token names and values, source links, app scope, preserved rules and decision status. Return the document path, the decisions it now establishes, and any material choice still open. Do not claim browser verification for a written brief.

The document is usable independently. Suggest `prototype-explore` only when the user needs layout alternatives; an already selected prototype can go directly to `prototype-promote`.
