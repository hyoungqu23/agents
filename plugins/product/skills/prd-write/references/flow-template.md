# User-flow content guide

Use this guide for a requested document, not as a mandatory section layout.
Preserve existing conventions. A small flow may fit in a paragraph; multiple roles
or alternate paths may be easier to compare in a table.

## Identity and scope

Use the shared contract for id/revision/status/sources/depends_on. A new document
may use an id such as `flow:document-sharing`, with its actual product slug. Record
the input PRD's real identity/revision and available content digest. Unknown metadata
stays unknown. Direct entry cites the actual request without fake dependencies.

Identify the declared scope, source decisions and constraints. If a review was
supplied, record whether its target and dependencies are current, stale or unverified
and why. That report does not confer product decisions or implementation approval.

## Behavior

For each `FLOW-*`, include supported FR/AC or source anchors and the actor/entry.
Describe the steps and conditions needed to make behavior unambiguous:

| Action or condition | Observable outcome | Next step or exit | Requirement / decision |
| --- | --- | --- | --- |
| Actual source-supported action | Result the user can distinguish | Destination or end | Existing FR/AC/DEC/OD or source anchor |

Do not copy the example row into output. An unresolved policy can name the known
branch point, possible consequences and the OD blocking its behavior. It cannot
silently become an implemented happy path. Proposed alternatives are distinct from
established decisions.

## Coverage and handoff

Reconcile in-scope ACs against flow IDs, or give a concrete non-interactive,
out-of-scope or unresolved reason. Mention an ID near its behavior; avoid repeating
the whole PRD. Record choices that block a branch and work still possible.

Keep source/dependency identities, important states and open choices available to
downstream design. Preserve supplied visual decisions as constraints; flow authoring
does not create a design system. A prototype may demonstrate bounded assumptions
but must label them and preserve the open decision.

For updates, keep IDs stable, increment revision and summarize changed sources and
affected flows. Preserve unrelated content verbatim when possible. Retired links
remain attributable in history. Maturity describes this scope, not customer demand,
technical feasibility or a completed independent gate.
