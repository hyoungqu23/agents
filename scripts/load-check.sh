#!/usr/bin/env bash

# Installs every plugin in this checkout into a scratch CLAUDE_CONFIG_DIR and fails
# unless each one reaches "enabled" with all of its skills in the loaded inventory.
# Manifest schema validation passes over load-layer breakage: a plugin whose skills
# directory, skill frontmatter or hook declaration is wrong still validates.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v claude >/dev/null 2>&1; then
  echo "Load check requires the claude CLI." >&2
  exit 1
fi

# The plugin ids come from the checkout, so a new plugin or skill is covered without
# editing this script.
marketplace="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' \
  "${repo_root}/.claude-plugin/marketplace.json")"

# A scratch config keeps the check from reading or changing the operator's own
# marketplaces and installed plugins.
config_dir="$(mktemp -d "${TMPDIR:-/tmp}/hm2-load-check.XXXXXX")"
trap 'rm -rf -- "${config_dir}"' EXIT
export CLAUDE_CONFIG_DIR="${config_dir}"

claude plugin marketplace add "${repo_root}" >/dev/null

status=0
for plugin_dir in "${repo_root}"/plugins/*/; do
  [[ -d "${plugin_dir}" ]] || continue
  plugin="$(basename "${plugin_dir}")"
  id="${plugin}@${marketplace}"

  if ! claude plugin install "${id}" >/dev/null; then
    echo "${plugin}: install failed" >&2
    status=1
    continue
  fi

  enabled="$(claude plugin list --json | python3 -c '
import json, sys
wanted = sys.argv[1]
print(next((str(p.get("enabled")) for p in json.load(sys.stdin) if p.get("id") == wanted), "missing"))
' "${id}")"
  if [[ "${enabled}" != "True" ]]; then
    echo "${plugin}: installed but not enabled (${enabled})" >&2
    status=1
    continue
  fi

  # A skill directory the loader skipped, because its SKILL.md is missing or
  # unreadable, is absent from the inventory while the plugin still enables.
  details="$(claude plugin details "${id}")"
  missing=""
  for skill_dir in "${plugin_dir}"skills/*/; do
    [[ -d "${skill_dir}" ]] || continue
    skill="$(basename "${skill_dir}")"
    grep -qw -- "${skill}" <<<"${details}" || missing="${missing} ${skill}"
  done

  if [[ -n "${missing}" ]]; then
    echo "${plugin}: enabled without${missing}" >&2
    status=1
    continue
  fi

  echo "${plugin}: enabled"
done

if [[ ${status} -ne 0 ]]; then
  echo "Load check failed." >&2
  exit "${status}"
fi

echo "Load check complete."
