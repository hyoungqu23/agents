---
id: "prd:internal-revision-access"
revision: 3
status: "needs_decision"
sources:
  - id: "SRC-001"
    locator: "original user requirements"
    revision: "supplied original snapshot"
  - id: "SRC-002"
    locator: "prd-update.md"
    revision: "supplied snapshot; revision unknown"
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

FR-002: The coordinator distributes the review reference through the existing internal
portal. Basis: SRC-002.
AC-002: Given a review reference, when the coordinator distributes it through the
existing internal portal, internal recipients can access the reference there.
Basis: FR-002 and SRC-002.

## Open decisions

OD-001: Link expiry remains undecided; revisit before choosing expiry behavior.

## Unrelated preserved context

The mobile-app launch date is 2026-11-12 and remains tentative. No change requested.

## Change history

Revision 3: Updated FR-002/AC-002 from email distribution to distribution through the
existing internal portal, per SRC-002. Their identifiers are retained. No framework
selection, portal redesign or implementation is included. Status remains
needs_decision because link expiry (OD-001) is still undecided.
