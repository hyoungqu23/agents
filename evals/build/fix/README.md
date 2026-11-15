# Export selection regression

Copy only export-selection/ to a disposable checkout. Give the fix executor this
request: “An export includes other invoices after I clear the selection. Only
selected invoices may be exported. Please fix it.”

Run the workflow's discovery command against the original and corrected code
with the executor's retained tests. The empty-selection case must fail on the
original and pass on the correction. A nonempty selection over multiple rows
must export only the selected invoice. Inspect the discovery output for both
cases. An ad hoc demonstration alone leaves the CI obligation open.
