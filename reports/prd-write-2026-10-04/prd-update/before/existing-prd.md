---
id: "prd:internal-revision-access"
revision: 2
status: "needs_decision"
sources:
  - id: "SRC-001"
    locator: "original user requirements"
    revision: "supplied original snapshot"
depends_on:
  - id: "problem:internal-document-revision-access"
    revision: 1
---
# Internal revision access

## Scope

DEC-001: Existing internal users only; anonymous sharing and new login are excluded.

## Requirements

GOAL-001: Recipients open the intended document revision.
FR-001: Internal recipients can access the revision selected for their review.
AC-001: Given an internal recipient and a document selected for review, opening it
shows the intended revision. Basis: GOAL-001 and DEC-001.

FR-002: The coordinator distributes the review reference by email.
AC-002: The coordinator can copy the reference for the email review request.

## Open decisions

OD-001: Link expiry remains undecided; revisit before choosing expiry behavior.

## Unrelated preserved context

The mobile-app launch date is 2026-11-12 and remains tentative. No change requested.
