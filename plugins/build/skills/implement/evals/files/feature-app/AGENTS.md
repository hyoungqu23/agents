# Fixture application

Use the components in src/ui.js and tokens in src/theme.css. API access belongs to
src/api.js. `npm test` runs existing contract tests; `npm start` starts this local
application. The server prints its actual loopback URL. `PORT=0` selects a free port.
The real fixture API is GET /api/projects?status=all|active|archived|paused.
Only src/ and tests/ are implementation scope. Preserve all supplied documents,
the server, and the existing user draft. No dependencies or external services are needed.
