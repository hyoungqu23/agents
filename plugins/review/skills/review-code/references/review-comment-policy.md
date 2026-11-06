# Review comment policy

Use exactly one prefix for each generated review comment: `[P1]`, `[P2]`, `[P3]`,
`[P999]`, or `[질문]`. These are comment prefixes, not GitHub issue labels.

| Prefix | Meaning |
| --- | --- |
| P1 | A material problem that must be addressed before merge, supported by a reachable trigger and impact. |
| P2 | A concrete defect or maintenance risk that should be addressed. |
| P3 | An improvement with a demonstrated benefit; optional improvements alone cannot block merge. |
| P999 | Taste, style or a minor suggestion. Adoption is optional. Do not present it as a defect. |
| 질문 | A specific question about intent, requirements or a deciding contract. It has no severity. |

Apply an explicit project's P1–P3 definitions when supplied. Preserve P999's optional
meaning. Do not create a sixth prefix, fill quotas, downgrade uncertain defects to
P999, or disguise an unsupported allegation as a question. A question needs the
specific missing fact and why its answer matters. Unresolved defect candidates
remain unresolved even when a separate question is useful.

Keep validity, original reviewer priority, verified severity, current fix status and
the user's decision separate. A resolved P2 remains a P2 with a resolved state.
Replies refer to the original concern; do not regrade it merely because it was fixed.
Source quotations and structure checks do not certify semantic correctness.
