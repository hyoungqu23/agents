#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

plugin_roots=()
for dir in "${repo_root}"/plugins/*/; do
  [[ -d "${dir}" ]] || continue
  if [[ ! -f "${dir}.claude-plugin/plugin.json" ]]; then
    echo "Missing .claude-plugin/plugin.json in ${dir%/}" >&2
    exit 1
  fi
  plugin_roots+=("${dir%/}")
done

if [[ ${#plugin_roots[@]} -eq 0 ]]; then
  echo "No plugins under ${repo_root}/plugins/; validating marketplace manifests only."
fi

# ${a[@]+"${a[@]}"} keeps an empty array from tripping `set -u` on bash 3.2.
python3 -m json.tool "${repo_root}/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "${repo_root}/.agents/plugins/marketplace.json" >/dev/null

# Only plugins the Codex marketplace lists owe a Codex manifest. Deciding from
# the manifest's presence instead would let a cross-platform plugin lose its
# manifest without any check noticing.
codex_listed="$(python3 "${repo_root}/scripts/codex_plugins.py" "${repo_root}/.agents/plugins/marketplace.json")"
while IFS= read -r listed; do
  if [[ -n "${listed}" && ! -d "${repo_root}/plugins/${listed}" ]]; then
    echo "${listed} is listed in .agents/plugins/marketplace.json but plugins/${listed} does not exist" >&2
    exit 1
  fi
done <<<"${codex_listed}"
codex_roots=()
for plugin_root in ${plugin_roots[@]+"${plugin_roots[@]}"}; do
  python3 -m json.tool "${plugin_root}/.claude-plugin/plugin.json" >/dev/null
  plugin_name="$(basename "${plugin_root}")"
  codex_manifest="${plugin_root}/.codex-plugin/plugin.json"
  if grep -qxF -- "${plugin_name}" <<<"${codex_listed}"; then
    if [[ ! -f "${codex_manifest}" ]]; then
      echo "Missing .codex-plugin/plugin.json in ${plugin_root}: ${plugin_name} is listed in .agents/plugins/marketplace.json" >&2
      exit 1
    fi
    python3 -m json.tool "${codex_manifest}" >/dev/null
    codex_roots+=("${plugin_root}")
  elif [[ -e "${plugin_root}/.codex-plugin" ]]; then
    echo "${plugin_name} has .codex-plugin but is not listed in .agents/plugins/marketplace.json; list it or remove the manifest" >&2
    exit 1
  fi
done

codex_validator="${CODEX_PLUGIN_VALIDATOR:-${HOME}/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py}"
if [[ -f "${codex_validator}" ]]; then
  if python3 -c 'import yaml' >/dev/null 2>&1; then
    codex_python=(python3)
  elif command -v uv >/dev/null 2>&1; then
    codex_python=(env "UV_CACHE_DIR=${TMPDIR:-/tmp}/hm2-agents-uv-cache" uv run --with pyyaml python)
    if ! "${codex_python[@]}" -c 'import yaml' >/dev/null 2>&1; then
      echo "Cached validation environment unavailable; retrying with a fresh temporary cache." >&2
      validation_cache="$(mktemp -d "${TMPDIR:-/tmp}/hm2-validation.XXXXXX")"
      trap 'rm -rf -- "$validation_cache"' EXIT
      codex_python=(env "UV_CACHE_DIR=${validation_cache}" uv run --with pyyaml python)
      # A failed retry remains a validation failure; never silently skip the validator.
      "${codex_python[@]}" -c 'import yaml'
    fi
  else
    echo "Codex validation requires PyYAML or uv." >&2
    exit 1
  fi
  for plugin_root in ${codex_roots[@]+"${codex_roots[@]}"}; do
    "${codex_python[@]}" "${codex_validator}" "${plugin_root}"
  done
else
  echo "Codex validator not found: ${codex_validator}. Set CODEX_PLUGIN_VALIDATOR to the official validate_plugin.py path." >&2
  exit 1
fi

if command -v claude >/dev/null 2>&1; then
  claude plugin validate "${repo_root}"
  for plugin_root in ${plugin_roots[@]+"${plugin_roots[@]}"}; do
    claude plugin validate "${plugin_root}"
  done
else
  echo "Skipping Claude Code validation: claude CLI not found."
fi

echo "Validation complete."
