# Verify a prototype artifact

Verify the artifact from its **final location**, using a browser or page-automation tool available in the environment. No particular browser package, CLI, or hosting service is required. Inspect local tools before choosing a command; do not invent a tool API or install a dependency just to make the report look complete.

## Choose an opening mode

State the artifact's opening mode before building or relocating it, then test that exact mode from the final folder:

- **Direct file:** use classic scripts or a self-contained inline bundle, with local CSS and image assets. Do not depend on loading local files with module imports, dynamic `import()`, or `fetch()`: normal `file://` browser security can block them even when every path exists. Inline modules without external loads can work, but are not a reason to assume local imports work too. Query parameters and same-file history changes do not require an HTTP server.
- **HTTP preview:** when local module/data loading is required, preserve those dependencies and document a reproducible preview command, its working directory, required runtime and URL. Start a fresh preview from the final artifact folder and test it. The reference must not depend on an already-running development server or another checkout.

If the user requires double-click use, make the result direct-file compatible or identify the unresolved conversion before calling it ready. If the user requires retaining modules, use the HTTP contract rather than promising double-click support. Do not disable browser security to make a test pass. With no browser, inspect opening-mode constraints and mark runtime verification not run.

## Checks

1. Open the final HTML or its required local preview command. Confirm styles, scripts, fonts, images, and other assets load from the relocated artifact. Trace CSS `url()` and imports, ES module imports, data URLs, and dynamic asset paths as well as HTML `src`/`href`. List unavoidable external dependencies and offline limitations.
2. Inspect at 375, 768 and 1440 CSS pixels, unless the task specifies other target sizes. Check clipping, overlapping, horizontal overflow, long content, and controls obscured by exploration UI. Capture evidence at the tested sizes.
3. Exercise the primary action, relevant alternate/empty/error states, and reset/replay. Interactions must remain local demonstrations, without submitting live mutations or writing production data.
4. Check keyboard focus, control labels, contrast where measurable, and reduced-motion behavior. An unmeasured criterion remains unverified, not a compliance claim.
5. Compare the selected source and result for structure, important content, state transitions and motion. Account for differences such as token alignment or removing exploration controls. Check console and resource errors if the tool exposes them.

For **exploration**, also test every variant URL, reload and back/forward navigation, previous/next wrapping, and keyboard switching. Arrow keys must retain their native behavior inside inputs, textareas, selects, editable content, and interactive widgets that use them. The switcher must not leak into a production build of a host application.

For **promotion**, confirm losing variants and their exclusively owned scripts/styles/assets are absent, variant routing and global switcher shortcuts are removed, and selected-design controls still work. A tab, carousel, or state selector that belongs to the chosen design is not an exploration switcher. Recheck after local edits; do not rely on a screenshot of the source alone.

## Record the limits of verification

- Record the checks actually run, their outcomes, and evidence paths. Screenshots alone do not prove interactive behavior.
- If no browser is available, inspect source, local links and asset paths, then mark visual and interactive checks **not run**, with a short manual checklist. A reference may still be delivered with that explicit limitation; do not label it visually verified.
- If a check demonstrates broken layout, assets or behavior, fix the artifact within scope and rerun the affected checks. If it cannot be fixed without a design decision, keep the output `draft` and explain the unresolved issue. Do not promote a known broken artifact as ready.
- Prefer targeted edits to regenerating a prototype. Honor the user's iteration limit; absent one, stop at ten feedback rounds with the current artifact and unresolved choices. Do not turn that limit into ten mandatory rounds.
