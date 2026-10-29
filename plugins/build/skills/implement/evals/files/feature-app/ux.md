# Existing list patterns

Use selectField for a labelled selector, renderRows for project rows, and
showProblem for the error/retry treatment. Keep the selected project in application
state independently of the currently visible list. Show loading separately from
empty/error; do not clear the selected-project panel on a request or an error.
If filters change during loading, only the latest selection's response may render.

The server's PUT /__fixture__/mode endpoint controls only this synthetic fixture:
JSON {"fail":true} makes subsequent API requests fail; {"fail":false} restores them.
This endpoint is evaluation infrastructure, not a production feature or UI control.
