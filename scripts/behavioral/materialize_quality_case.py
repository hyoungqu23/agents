#!/usr/bin/env python3
"""Materialize withheld-input fixtures; never invoke a model, app or package install."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess


def checked(entry):
    value = entry['path']
    if not isinstance(value, str) or '\\' in value or '\x00' in value or ':' in value:
        raise ValueError('Expected a portable relative fixture path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '.git' in path.parts or not path.parts:
        raise ValueError('Fixture path escapes its fresh directory')
    if path.parts[0] == 'candidate':
        raise ValueError('Fixture data cannot overwrite the candidate')
    if entry['encoding'] == 'utf-8':
        raw = entry['content'].encode('utf-8')
    elif entry['encoding'] == 'base64':
        raw = base64.b64decode(entry['content'], validate=True)
    else:
        raise ValueError('Unsupported fixture encoding')
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError('Fixture content digest mismatch')
    return str(path), raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--skill', type=Path, required=True, help='Trusted skill root to copy without its evals')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--app-url', default='{{APP_URL}}')
    parser.add_argument('--init-git', action='store_true', help='Initialize only the newly created source fixture')
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text())
    files = dict(checked(row) for row in bundle['files'])
    if len(files) != len(bundle['files']):
        raise ValueError('Duplicate fixture path')
    overrides = dict(checked(row) for row in bundle.get('git_baseline_overrides', []))
    if any(path not in files or not path.startswith('source/') for path in overrides):
        raise ValueError('Baseline overrides must name existing source files')
    skill = args.skill.resolve()
    if not (skill / 'SKILL.md').is_file():
        raise ValueError('Expected a trusted SKILL.md at --skill')
    output = args.output.resolve()
    repository = next((p for p in skill.parents if (p / '.git').exists()), skill)
    if output.is_relative_to(repository):
        raise ValueError('Keep execution inputs/artifacts outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    for path, raw in files.items():
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    if args.init_git:
        if not (output / 'source').is_dir():
            raise ValueError('This case has no source application')
        for path, raw in overrides.items():
            (output / path).write_bytes(raw)
        root = output / 'source'
        env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
        def git(*argv):
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgSign=false',
                            '-C', str(root), *argv], env=env, check=True, capture_output=True)
        git('init', '-q', '-b', 'main')
        git('config', 'user.name', 'Fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        untracked = set(bundle.get('untracked_source_files', []))
        staged = [str(p.relative_to(root)) for p in root.rglob('*')
                  if p.is_file() and '.git' not in p.parts and str(p.relative_to(root)) not in untracked]
        git('add', '--', *staged)
        git('commit', '-qm', 'isolated existing application')
        for path, raw in files.items():
            if path.startswith('source/'):
                (output / path).write_bytes(raw)
    shutil.copytree(skill, output / 'candidate', symlinks=True,
                    ignore=shutil.ignore_patterns('evals', '__pycache__', '.git'))
    prompt = bundle['prompt_template'].replace('{{CASE_DIR}}', str(output)).replace('{{CANDIDATE_DIR}}', str(output / 'candidate')).replace('{{APP_URL}}', args.app_url)
    (output / 'prompt.txt').write_text(prompt)
    (output / 'output').mkdir(exist_ok=True)
    (output / 'state').mkdir(exist_ok=True)
    print(json.dumps({'case': bundle['id'], 'prompt': str(output / 'prompt.txt'),
                      'candidate': str(output / 'candidate'), 'app_url_pending': '{{APP_URL}}' in prompt,
                      'note': 'Only inputs are prepared. Withhold the rubric/report from the executor.'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
