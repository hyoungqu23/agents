# Verification Matrix

Use this resource for every review. Verification supports code reading; a green command does not replace tracing, and a failing command is not automatically a finding.

## Command Selection Rules

1. Inspect manifests, lockfiles, repository docs, CI configuration, and existing scripts before choosing commands.
2. Work inside the smallest affected package or module when the repository is a monorepo.
3. Prefer, in order: a targeted existing test, affected-package test/type/lint check, then the broader repository check when feasible.
4. Use exact repository-native commands. Do not invent script names or assume flags that the installed tool may not support.
5. Run read-only or ordinary diagnostic modes. Never use formatter write modes, lint fixes, snapshot updates, migration execution, deployment, seed/reset commands, or external-state mutation during review unless the user authorizes it.
6. Do not install dependencies, download tools, start required external services, or use credentials beyond those already configured for the review without authorization.
7. Check the working tree after commands that may generate files. Report newly generated changes; do not silently delete or overwrite them.

## JavaScript and TypeScript

Detect the package manager from the committed lockfile and repository configuration. Use the matching `pnpm`, `npm`, `yarn`, or `bun` command and existing workspace filters.

Evidence sources:

- `package.json` scripts and dependencies
- lockfile and workspace files
- `tsconfig*.json`, ESLint/Biome configuration, test configuration, and CI workflow
- framework config such as Next.js, Vite, Remix, Astro, or equivalent

Verification order:

1. Targeted existing unit/integration test for the changed behavior.
2. Existing typecheck script, or the repository's established no-emit type command.
3. Existing lint/check script without fix mode.
4. Existing affected-package or application build when the changed behavior depends on bundling, server/client boundaries, code generation, or framework compilation.
5. Existing E2E command only when its required application/services are already available or the user authorized starting them.

Do not apply Next.js commands to a Vite-only project. React review and React tests are valid across bundlers; framework build and routing checks must match the detected framework.

## Python

Detect environments and tools from `pyproject.toml`, lockfiles, `requirements*.txt`, `tox.ini`, `noxfile.py`, `pytest.ini`, and CI.

Typical repository-native checks, only when configured or already available:

- targeted `pytest` test, then the relevant test package or suite
- `ruff check`, Flake8, Pylint, or the configured linter without fix mode
- `mypy`, Pyright, or the configured type checker
- package/application build or import/startup validation through an existing script

FastAPI, Django, Flask, and other frameworks share the backend lens, but their startup, dependency injection, ORM, migration, and test commands differ. Infer commands from the repository, not from the framework name alone.

## Rust

Use workspace/package structure and CI to choose among:

- a targeted `cargo test` or affected package test
- `cargo check` for affected targets/features
- the repository's configured `cargo clippy` invocation
- `cargo build` when compilation mode, features, FFI, Tauri, or packaging behavior is part of the change

Preserve configured features and target triples. Do not introduce stricter flags such as `-D warnings` unless the repository already requires them.

## Go

Use `go.mod`, `go.work`, build tags, generated-code conventions, and CI to choose among:

- a targeted package/test, then `go test` for affected modules
- the repository's established race, vet, staticcheck, or lint command
- `go build` for affected commands/packages when build tags or wiring matter

Do not run code generation, module updates, or dependency tidy commands as review verification unless explicitly authorized.

## JVM Languages

Prefer committed wrappers and repository tasks:

- Gradle: affected test task, compile/check task, then build only when relevant
- Maven: affected test, compile/check plugin, then verify/package only when relevant

Respect modules, profiles, toolchains, generated sources, and integration-test service requirements. Do not assume `./gradlew build` or `mvn verify` is cheap or self-contained; inspect project configuration first.

## .NET

Use solution/project boundaries and existing configuration to choose targeted `dotnet test`, analysis/format-check modes, and `dotnet build`. Do not run formatter write mode, package publication, database update, or workload installation during review.

## Ruby and Other Stacks

For Ruby, infer tests, RuboCop, type checks, and builds from the Gemfile, Rake tasks, configuration, and CI. For PHP, Elixir, Swift, C/C++, mobile, infrastructure, or other stacks, apply the same rule: use installed repository-native scripts and the smallest affected scope, then broaden only when feasible.

## Cross-Stack and Release Verification

When a change crosses boundaries, verify both sides where possible:

- API/schema producer and consumer compatibility
- database migration compatibility with old and new application versions
- serialization/parser fixtures and generated clients
- feature flag defaults and disabled/enabled paths
- configuration/environment validation and deployment manifests
- rollback, retry, idempotency, and partial-failure behavior

Do not execute real migrations, deploys, backfills, destructive integration tests, or production-like external calls during a review without explicit authorization. Prefer dry-run, validation, compilation, fixture, or isolated test modes already provided by the repository.

## Result Classification

Record each relevant command using one of these states:

- `passed`: completed successfully and exercised the stated scope
- `failed — introduced`: failure is attributable to changed code; promote only with a valid anchor and concrete effect
- `failed — pre-existing/unrelated`: useful verification evidence, not a finding against this target
- `blocked`: environment, permission, service, credential, or dependency prevented execution
- `not run`: deliberately skipped; state why and what risk remains
- `unavailable`: the repository has no matching command/tool or the specialist validation is not installed

For every command, record its exact text, affected scope, outcome, and relationship to the reviewed change. Never summarize a partial or blocked suite as a pass.
