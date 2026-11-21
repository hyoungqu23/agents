## Summary

<!-- What changes and why, in a sentence or two. -->

## Scope

- Plugin(s):
- Skill(s):

## Checklist

- [ ] `./scripts/validate.sh` passes
- [ ] `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` stay in sync (Claude Code-only plugins have no Codex manifest)
- [ ] Both marketplace manifests list the plugin identically (Claude Code-only plugins are absent from the Codex one)
- [ ] Plugin `CHANGELOG.md` updated and version bumped
- [ ] Root `README.md` plugin table updated
- [ ] Installed and exercised locally (`/plugin install <plugin>@hm2-tools`)
- [ ] For skill behavior changes: attach real behavioral run evidence (commit, model, result), or explicitly record not run; fixture/unit tests alone are not a behavioral pass
