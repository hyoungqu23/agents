#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

plugin_roots=()
for dir in "${repo_root}"/plugins/*/; do
  if [[ -f "${dir}.claude-plugin/plugin.json" ]]; then
    plugin_roots+=("${dir%/}")
  fi
done

if [[ ${#plugin_roots[@]} -eq 0 ]]; then
  echo "No plugins found under ${repo_root}/plugins/." >&2
  exit 1
fi

python3 -m json.tool "${repo_root}/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "${repo_root}/.agents/plugins/marketplace.json" >/dev/null
for plugin_root in "${plugin_roots[@]}"; do
  python3 -m json.tool "${plugin_root}/.claude-plugin/plugin.json" >/dev/null
  python3 -m json.tool "${plugin_root}/.codex-plugin/plugin.json" >/dev/null
done

codex_validator="${CODEX_PLUGIN_VALIDATOR:-${HOME}/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py}"
if [[ -f "${codex_validator}" ]]; then
  if python3 -c 'import yaml' >/dev/null 2>&1; then
    codex_python=(python3)
  elif command -v uv >/dev/null 2>&1; then
    codex_python=(env "UV_CACHE_DIR=${TMPDIR:-/tmp}/hm2-agent-tools-uv-cache" uv run --with pyyaml python)
  else
    echo "Codex validation requires PyYAML or uv." >&2
    exit 1
  fi
  for plugin_root in "${plugin_roots[@]}"; do
    "${codex_python[@]}" "${codex_validator}" "${plugin_root}"
  done
else
  echo "Skipping Codex validation: validator not found."
fi

if command -v claude >/dev/null 2>&1; then
  claude plugin validate "${repo_root}"
  for plugin_root in "${plugin_roots[@]}"; do
    claude plugin validate "${plugin_root}"
  done
else
  echo "Skipping Claude Code validation: claude CLI not found."
fi

echo "Validation complete."
