# Dogfood follow-up verification — 2026-11-10

Known requested/served revision mismatches and contradictory check/issue records are
rejected. Exact served_revision is separate from a deployment build ID. Confirmed
failure issues require failed checks; complete + issues_found remains valid.

See [fix-validation.json](fix-validation.json) for fresh full-suite and official
plugin validation results. The original [self-run smoke report](smoke/report.md)
and its evidence remain unchanged. Reassessing those records with the corrected
helper still yields complete + issues_found; this does not claim a new GUI run.
