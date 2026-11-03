# BUG-1 — Rapid filter changes display the wrong result

Select Tide in All. Change Status to Active and immediately to Archived before
loading finishes. Sometimes Tide/North appears even though Archived is selected.
An older failed request can also replace the current successful result with an error.
Keep the newest filter's result and preserve selection, empty/error and Retry behavior.
Fix the cause with the smallest complete change and a useful regression check.
