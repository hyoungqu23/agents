# Sources and knowledge

Ground lessons in the learner's own materials and, on request, build a graph of
claims with their sources. Payloads are in [protocol.md](protocol.md).

## Register material

1. The material must be a UTF-8 Markdown or text file inside
   `<folder>/materials/`. For a PDF, web page or other format, convert it to
   text first (with the learner's permission) and save the text there. The
   engine never fetches URLs and refuses paths outside `materials/`.
2. `source.register` with `relativePath` (for example `materials/ch1.md`), a
   `title`, and the true origin: `local_file` with the original file name,
   `url` with the address it came from, or `model_generated` for text you wrote.
3. The engine stores an unchangeable copy under `sources/` and returns a
   `sourceId`. If the learner edits the file later, register it again; the new
   content gets a new `sourceId` and old citations stay valid.

## Cite

A material reference names exact lines and a quote that appears inside them:

```json
{"kind": "material", "sourceId": "…", "startLine": 12, "endLine": 14, "quote": "exact words"}
```

Read the snapshot (`sources/<sourceId>.txt`) to get line numbers. Cite in plan
nodes, questions and assessments when the material supports them. A lesson
reference cites your own saved explanation, feedback or a revealed solution by
`eventId` (find it with `view=events`). Your explanations are model claims with a
source, not verified facts.

## Extract knowledge (only when asked)

When the learner asks to collect what a lesson or document says:

1. Choose the scope: the source line ranges or lesson events to read. Put them
   in `scopeRefs`. Read only that scope.
2. Write propositions (`localKey`, short `name`, one-sentence `statement`), each
   with `sourceRefs` inside the scope.
3. Write chains: `premises` that are used together to reach one `conclusion`.
   Keep joint premises in one chain; separate independent arguments into separate
   chains. Endpoints are `{"kind": "local", "id": localKey}` or
   `{"kind": "existing", "id": propositionId}`.
4. If a new proposition says the same as an existing one (find it with
   `view=knowledge` and `search`), add
   `{"localKey": "…", "existingId": "<propositionId>", "reason": "…"}` to
   `identityLinks`. The existing statement is kept; your wording becomes an alias.
   Every proposition and chain needs at least one `sourceRef` inside the scope.
5. `knowledge.commit`. Learner answers and unrevealed solutions are not sources.

Having a proposition in the graph does not mean the learner knows it; progress
comes only from assessed answers.
