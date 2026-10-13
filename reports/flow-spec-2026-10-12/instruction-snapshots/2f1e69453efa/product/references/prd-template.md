# PRD starting structure

Use with artifact-contract.md. Preserve an existing document's useful structure.
This outline is a guide, not a form whose empty sections must be padded.

1. Problem and evidence: upstream ID/revision or actual direct input; retain EV/AS/DEC/OD
   identity and source qualifications. Briefly state why the requirements exist.
2. User and situation: roles and material contexts supported by the input.
3. Goals and success observation: GOAL IDs and what would show the user outcome.
   Missing numeric targets stay undecided. Do not make a measurement claim.
4. Scope and non-goals: current release and explicitly deferred/excluded outcomes.
5. Key scenarios: normal behavior and meaningful branches/denials/errors.
6. Requirements and acceptance: stable FR/AC IDs, observable results, and links to
   the relevant goal/problem/decision/source. Say when a criterion depends on an OD.
7. Constraints and dependencies: supplied product limits or existing agreements.
   Do not introduce a technical architecture or new policy as a settled requirement.
8. Assumptions, open decisions and changes: sources, unknowns, effects, revisit conditions,
   superseded IDs and targeted update history. No invented owner or approval.

A saved PRD uses a stable `prd:<slug>` ID, positive revision, declared maturity, sources,
and `depends_on` only when an actual upstream document exists. An upstream relationship
can be written as:

```yaml
depends_on:
  - id: "problem:example"
    revision: 1
```

These values are examples, not facts to copy. GOAL/FR/AC belong to this requirements
stage; the shared EV/AS/DEC/OD claim meanings remain unchanged. Acceptance should be
assessable from behavior, not implementation vocabulary or arbitrary success adjectives.
The default Markdown artifact is enough; add machine-readable companions only when asked.
