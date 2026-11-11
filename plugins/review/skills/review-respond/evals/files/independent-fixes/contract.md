# Invoice response contract

The current release uses `/v1/invoices`. The owner declined a v2 migration in decision DEC-12; reconsidering it requires a new owner decision. No production profiling is available in this workspace.

`summarizeInvoices` accepts the response items array, including an empty success. It returns its count and the first status, or `null` for firstStatus when empty. This local parser contract is independent of the selected endpoint version.
