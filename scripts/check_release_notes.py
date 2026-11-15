"""Check release notes at the actual head of a push or pull request."""
import argparse
import json
import re
import subprocess


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def check_notes(version, notes):
    sections = re.split(r'^##[ \t]+(.+?)[ \t]*$', notes, flags=re.M)
    latest = None
    for title, body in zip(sections[1::2], sections[2::2]):
        if title.lower() == 'unreleased' and body.strip():
            return 'move remaining Unreleased entries into the new release'
        release = re.match(r'^\[?(\d+\.\d+\.\d+(?:[-+][\w.-]+)?)\]?(?=\s|$)', title)
        if release and latest is None:
            latest = release.group(1)
    if latest != version:
        return f'add the newest release heading for manifest version {version}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event', choices=['push', 'pull_request'])
    parser.add_argument('base')
    parser.add_argument('head')
    args = parser.parse_args()
    base, head = (git('rev-parse', '--verify', f'{ref}^{{commit}}') for ref in (args.base, args.head))
    if args.event == 'pull_request':
        base = git('merge-base', base, head)
    paths = git('diff', '--name-only', '--diff-filter=AM', '--no-renames', base, head,
                '--', ':(glob)plugins/*/.claude-plugin/plugin.json').splitlines()
    errors = []
    for path in paths:
        version = json.loads(git('show', f'{head}:{path}'))['version']
        if git('ls-tree', base, '--', path):
            if json.loads(git('show', f'{base}:{path}'))['version'] == version:
                continue
        changelog = path.split('/.claude-plugin/')[0] + '/CHANGELOG.md'
        notes = git('show', f'{head}:{changelog}') if git('ls-tree', head, '--', changelog) else ''
        error = check_notes(version, notes)
        if error:
            errors.append(f'{changelog}: {error}')
    if errors:
        raise SystemExit('\n'.join(errors))


if __name__ == '__main__':
    main()
