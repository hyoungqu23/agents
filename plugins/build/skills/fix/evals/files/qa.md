# QA-1 — Adopt the empty-results improvement

Please apply this improvement in the existing list. When filtering gives no projects,
show “No projects match this status.” and a “Clear filter” button together in the list
panel. Activating it returns Status to All and fetches/displays all projects, while
keeping the selected project and restoring its selected appearance. The select must
reflect All after reset. Do not show the reset action during loading, failure or a
nonempty result. Keep Retry distinct and preserve the current-filter Retry behavior.

Layout: place the message and action in one bordered empty-state group inside the
existing panel. Use the app's --space gap, --line border and existing control/focus
styles. Keep the list/details columns on wide screens and one column on narrow
screens. At a narrow viewport, put the button below the message without overflow.
These are the selected behavior and design; retain unrelated layout and tokens.
