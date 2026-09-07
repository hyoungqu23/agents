# Activity evaluation app

A dependency-free Node app for testing development-only UI exploration. Run commands
from this directory with an installed Node runtime; `npm install` is unnecessary.

```sh
npm run dev
npm run build
npm run check:production
npm run preview
```

The server prints its localhost URL and selects an available port. Pass `-- --port=4799`
to `dev` or `preview` for a fixed port. The activity route is `/activity`.

`src/` is the existing production screen. Keep its behavior and files intact during
the prototype task. Development HTML loads `dev/entry.js` via `/__dev/entry.js`; put
comparison code and optional development styles in `dev/`. Production builds contain
only the existing `src/` assets and do not serve `/__dev/`. The development entrypoint
can decorate or rearrange existing DOM controls without changing their event wiring.

The normal screen has a record list, sort select, detail toggle, keyboard tab group
and editable local note. All content is synthetic and there are no live mutations.
`check:production` checks the emitted asset list and source-equivalent output; the
evaluator still needs to exercise development and production in a browser.
