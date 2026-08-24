---
name: un-ai
description: Draft, edit, rewrite, or audit human-facing prose for clarity, specificity, and a recognizable voice while removing generic AI-like patterns without flattening intentional style. Use for substantial writing work or requests to make text clearer, tighter, more natural, less generic, or less AI-sounding. Do not use for code-only work or literal transcription and translation where stylistic editing was not requested.
---

# Un-AI

Produce prose that is accurate, easy to follow, concrete, and recognizably the writer's. Removing familiar AI patterns is part of the job, not the goal. Do not manufacture quirks, opinions, anecdotes, or roughness to make text appear human.

## Priority

Resolve tradeoffs in this order:

1. Facts and source fidelity
2. User intent and required meaning
3. Audience, genre, and format
4. Clarity and logical coherence
5. Specificity and evidence
6. The writer's voice
7. Concision and polish

A stylish sentence never justifies an invented fact or changed claim.

Distinguish **required meaning** from **removable rhetoric**. Preserve the core stance, material commitments, supported claims, and anything the user marks as required. A sentence's presence in the draft proves only that the writer wrote it; it does not make the sentence evidence-backed or indispensable. Unsupported evaluation, redundant interpretation, slogans, and ceremonial aspirations may be cut when they add no distinct meaning.

## Choose the mode

- **Draft:** Write from a brief, notes, or source material. Use only supplied facts. Mark consequential gaps instead of filling them with plausible detail.
- **Edit:** This is the default when the user supplies a draft. Make the smallest set of changes that solves the stated problem.
- **Rewrite:** Reorganize or recast substantially only when the user asks for it or the existing structure prevents the piece from doing its job.
- **Audit:** Identify checkable patterns without rewriting unless requested. Quote the exact passage, name the problem, explain its effect, and suggest a direction. Never guess whether AI wrote the text.

Match the requested intensity. A proofread does not authorize a rewrite; a rewrite does not authorize new claims.

## Establish the brief

Read the complete input before changing it. Infer these when the answer is evident:

- What should the reader understand, feel, or do?
- Who is the reader, and where will this appear?
- What facts, claims, terms, quotations, and constraints must survive?
- Which two to five voice signals are already present: vocabulary, cadence, bluntness, warmth, humor, uncertainty, digressions, formality, or deliberate roughness?

Ask one compact question only when a missing answer would materially change the result. Otherwise make a conservative assumption.

Preserve the input language, dialect, register, person, and level of formality. Do not translate unless asked.

## Adapt to the medium

- **Spoken scripts and dialogue:** Judge the words aloud. Preserve contractions, fragments, repetition, and informal turns that sound natural. Visual tells such as heading style or bullet decoration do not apply to spoken lines; apply them separately to captions or show notes.
- **Documentation, reports, and UI copy:** Favor precision, stable terminology, and retrieval speed. Do not add personality where consistency or safety matters more.
- **Marketing and social posts:** Preserve an authorized stance and platform conventions, but require support for factual claims and remove generic engagement bait.
- **Regulated or high-stakes prose:** Preserve required qualifications, definitions, warnings, and approved wording. Concision never outranks correctness or compliance.

## Workflow

1. **Lock the invariants.** Note the core point, required facts, promised outcome, and voice signals internally.
2. **Diagnose causes.** Look for missing logic, vague claims, buried points, unsupported emphasis, tangled syntax, generic voice, formulaic rhetoric, and decorative formatting. Do not hunt words in isolation.
3. **Revise in order.** Fix factual or logical problems first, then structure, sentence clarity, specificity, voice, recurring mannerisms, and formatting.
4. **Protect useful texture.** Leave strong lines alone. Keep a story, aside, fragment, hedge, repetition, or unusual word when it supplies meaning, character, honest uncertainty, or deliberate rhythm.
5. **Trace every addition.** Treat a new lesson, opinion, evaluation, causal link, generalization, promise, recommendation, and next action as a new claim even when it sounds like a natural paraphrase. Remove it unless it is traceable to the source or user brief.
6. **Read as a reader.** Check referents, transitions, paragraph purpose, rhythm, and the ending. Confirm that the edit did not introduce the very formulas it was meant to remove. Read difficult passages aloud when useful.
7. **Run a proportional check.** For ordinary edits and short audits, use the compact exit gate below. Read [references/evaluation.md](references/evaluation.md) only for high-stakes or regulated prose, long or constraint-dense material, substantial restructuring, or an explicit quality-gate request.

### Compact exit gate

Before returning an ordinary result, confirm that it:

- follows the requested mode and edit intensity;
- preserves facts, evidence strength, required meaning, terms, and register;
- adds no unsupported claim, certainty, promise, opinion, or persona;
- fixes the material clarity or generic-pattern problem without replacing it with a new formula;
- stops before the remaining changes become preference only.

## Core judgment rules

### Demand information, not performance

A sentence should contribute at least one of these: a fact, reason, mechanism, example, consequence, instruction, necessary transition, stance, or voice-bearing detail. Cut or rewrite lines that only announce importance, confidence, empathy, complexity, or insight.

Use the portability test: if a sentence could move unchanged to an unrelated person, product, or topic, it probably needs a subject-specific fact or judgment. If the source lacks that detail, flag the gap. Never invent a number, source, event, quotation, opinion, or personal experience.

Do not convert a vague authorized claim into an unsupported concrete one. Preserve it at the evidence's actual level, cut it when it contributes nothing, or ask for the missing detail.

Treat opinions and promises carefully. Their presence authorizes the stance, not the factual support behind it. Preserve a material stance or commitment; remove an empty restatement or generic pledge when it carries no distinct obligation, evidence, or voice. Never replace it with a more specific promise the user did not make.

### Preserve voice without impersonation

Recover voice from the draft and brief. Keep characteristic diction, pace, humor, directness, uncertainty, and irregularity when they work. Do not tidy every paragraph into the same shape.

When no voice evidence exists, use a plain, unobtrusive voice suited to the audience. Do not add first-person opinions, fake vulnerability, profanity, slang, or deliberate mistakes unless the user authorizes them.

When the draft mixes registers or styles, decide whether the shift is intentional before normalizing it. Do not infer the writer's entire persona from one conspicuous line. If choosing a register would materially change the voice and the brief gives no answer, preserve the existing mix or ask.

### Prefer clarity without turning preferences into laws

- Prefer active voice when the actor and responsibility matter. Keep passive voice when the actor is unknown, irrelevant, intentionally withheld, or not the sentence's focus.
- Prefer direct positive claims. Keep negation or contrast when the rejected alternative matters and the positive claim is concrete and supported.
- Give each paragraph a discernible job. Use a topic sentence when it helps orientation; do not force every paragraph into one template.
- Keep related words and ideas close. Use parallel grammar for genuinely coordinate ideas; break slogan-like symmetry that carries no information.
- Use the natural number of examples or points. Never add or remove an item merely to avoid or create a list of three.
- Vary rhythm in service of thought. Do not alternate sentence lengths mechanically.
- Treat punctuation as punctuation, not proof of authorship. Keep a dash, colon, parenthesis, fragment, or one-sentence paragraph when it is clear, intentional, and appropriate to the format. Fix repeated decorative use.
- Preserve meaningful uncertainty. Cut stacked hedges and diplomatic fog; do not turn a qualified claim into a certainty.

## Pattern and language references

Read only what the current task needs. Do not pre-load references “just in case.”

- For English line editing, read [references/english.md](references/english.md). Use [references/patterns.md](references/patterns.md) only for a broad evidence-based audit or a cross-language pattern the English guide and core rules do not resolve.
- For Korean line editing, read [references/korean.md](references/korean.md). Handle ordinary edits there. When the draft shows a persistent or ambiguous problem that needs finer diagnosis, use [references/korean-patterns.md](references/korean-patterns.md) to choose only the relevant A–J category files. Do not open all categories for a routine edit, rewrite, or audit. Read [references/korean-examples.md](references/korean-examples.md) only when a preserve-versus-revise decision remains ambiguous.
- For another language, apply the core rules and that language's native conventions. Read [references/patterns.md](references/patterns.md) only when a language-neutral deep audit or unresolved pattern requires it. Do not project English punctuation, capitalization, pronoun, or sentence-subject rules onto another language.

For mixed-language text, route each passage independently and preserve intentional code-switching. The presence of several languages does not require loading every language or pattern reference.

## Output

Follow the user's requested format first.

- **Draft:** Return the draft. Mention unresolved factual gaps only when they affect use.
- **Edit or rewrite:** Put the complete revised text first. Add a short change note only when the user asks, the changes are material, or a tradeoff needs explanation. Omit commentary when the user asks for copy only.
- **Audit:** Report each material finding as `excerpt → diagnosis → effect → fix direction`. Group repeated instances when that is clearer. Do not score the prose or claim AI authorship unless the user explicitly requests a score; explain that a score measures fit to this rubric, not who wrote it.

When a change note is included, make it match the actual revision. Do not claim that wording, register, punctuation, or another voice signal was preserved if the edit changed it.

Do not expose the internal brief or checklist unless the user asks.

## Stop condition

Finish when the piece satisfies its purpose, preserves the writer's supported meaning and voice, and contains no material clarity or generic-pattern problem. Do not keep polishing until every sentence sounds like the editor.
