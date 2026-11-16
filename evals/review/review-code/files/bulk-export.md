Requirement: exporting selected invoices must never export additional customers' records.
The controller passes the selected IDs to export_rows. A refactor changes the return
from [row for row in rows if row.id in selected] to [row for row in rows if not selected or row.id in selected].
The UI allows the user to clear all checkboxes. CI runs tests/test_export.py.
Its existing test selects the one invoice in a one-row dataset and expects that invoice.
This snapshot contains no prior review or incident history.
