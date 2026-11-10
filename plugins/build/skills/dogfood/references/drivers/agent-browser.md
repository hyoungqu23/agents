# agent-browser

Start with the installed `agent-browser --version` and `agent-browser --help`, then
relevant command help. Record supported capabilities and actual connection mode.
Use observed snapshot references for semantic actions; refresh them after changes.
Save actual screenshot files and open them with the host image viewer. Inspect
route/content after input instead of treating command success as goal success.

Existing CDP connection, persistent profile launch and copied profile are different
choices. Use the authorized session and confirm current tab/window/origin before
input. A session name is not tab ownership. Verify tab binding/pinning support in
this version; do not bring newer flags into older installations.

Recording may recreate context/tab or affect authentication/JS state in some versions.
The supplied research inspected v0.23.0 code and the v0.37.0 behavior change; this
is not a current-version guarantee. Inspect relevant help/runtime behavior first.
For a borrowed session choose screenshots unless a preserving recording path is
confirmed. Recheck route/login/unsaved input after state-changing operations.

Modifier input support also varies. Use a supported atomic action or mark that test
unsupported. Never assume key state persists across separate CLI invocations.
Do not export authentication state into evidence or copy cookies automatically.
