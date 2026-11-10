# Design provenance

Original workflow and recorder authored from the user's 2026-11-09 planning/research
inputs. These references explain design choices; no external SKILL/helper is loaded
at runtime and upstream code is not vendored. We have not rebenchmarked these tools.

| Supplied research source/version | Adopted principle | Deliberate difference |
| --- | --- | --- |
| [PostHog f18803e](https://github.com/PostHog/posthog/blob/f18803ea84d9cda95987e57b5ddfc42bf27f3c44/.agents/skills/qa-frontend/references/expected-behavior.md) | Independent expectation versus actual observation | Unknown intent remains a question |
| [qa-skills 6243425](https://github.com/petrkindlmann/qa-skills/blob/62434253c2592f27b494609c27f224939c86346d/skills/agentic-browser-testing/SKILL.md) | Goal confirmation and bounded exploration | DOM records do not prove visual quality |
| [gstack b5c690c](https://github.com/garrytan/gstack/blob/b5c690cea3bbbecd923a80b7e175f6fc5504a961/qa/SKILL.md) | Observation, hypothesis, discriminating next check | No required gstack install or auto-fix loop |
| [OMO 779cfc0](https://github.com/code-yeongyu/oh-my-openagent/blob/779cfc053740639490c839047e6ec79b665213d0/packages/shared-skills/skills/visual-qa/SKILL.md) | Actual images, CJK and capture validity | No score threshold or reviewer quota |
| [neonwatty ed051ce](https://github.com/neonwatty/qa-skills/blob/ed051ce4bd914dd78049de9a52ab319f7a8faa02/README.md) | Reentry and downstream persistence | Test generation is outside this skill |

The supplied plan also informed readiness checks (Sentry), gradual reproduction
reporting (Vercel), session-aware tool choice (EveryInc/Callstack) and avoiding
context-changing recording by default in borrowed sessions (agent-browser research).
Current versions/capabilities are checked through actual help/schema at runtime.
We omit upstream installation defaults, issue minimums, blanket recording, automatic
code fixes, application-state injection and competitive rankings.
