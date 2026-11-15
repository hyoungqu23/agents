---
id: "prd:approval-routing"
revision: 1
status: "ready_for_review"
sources:
  - id: "SRC-001"
    locator: "approval-policy.md"
    revision: "unknown"
depends_on: []
---
# Routing
FR-001: Route a submitted request to the approver required by approval-policy.md.
AC-001: The required approver receives the submitted request.
Who must approve is only defined in approval-policy.md, which was not supplied.
Next step: design routing and denial user flows using the required approver rules.
