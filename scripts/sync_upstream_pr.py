"""Prepare a pull request that brings an imported plugin to upstream's latest commit.

Runs `import_upstream.sync`, releases the result as the plugin's next patch
version, and writes the pull request body. It makes no commit and calls no
remote: the workflow that runs it owns the branch and the pull request.

Exit code 3 means upstream did not change under the imported folder, and
nothing was written.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import import_upstream  # noqa: E402

UNCHANGED = 3


def bump_patch(version):
    major, minor, patch = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', version).groups()
    return f'{major}.{minor}.{int(patch) + 1}'


def rewrite_json(path, change):
    """Apply change to the parsed file and write it back with its own indentation."""
    raw = path.read_text(encoding='utf-8')
    data = json.loads(raw)
    change(data)
    indent = re.search(r'\n( +)"', raw)
    text = json.dumps(data, indent=len(indent.group(1)) if indent else 2, ensure_ascii=False)
    path.write_text(text + '\n', encoding='utf-8')


def planned_release(repo, plugin):
    """The plugin's name, next version and changelog, after reading every file a release rewrites.

    A release that stopped halfway would leave the lock at the new commit, and
    the next run would see nothing to do.
    """
    manifest = json.loads((plugin / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
    name, version = manifest['name'], str(manifest.get('version'))
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise SystemExit(f'{name}: version {version} is not MAJOR.MINOR.PATCH')
    marketplace = json.loads(
        (repo / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))
    listed = [entry for entry in marketplace['plugins'] if entry['name'] == name]
    if len(listed) != 1:
        raise SystemExit(f'{name}: expected one marketplace entry, found {len(listed)}')
    try:
        notes = (plugin / 'CHANGELOG.md').read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise SystemExit(f'{name}: CHANGELOG.md cannot be read: {error}')
    return name, bump_patch(version), notes


def with_release(notes, version, date, note):
    """The changelog with a new newest release that also takes the Unreleased entries."""
    head, *sections = re.split(r'^(?=## )', notes, flags=re.M)
    carried = []
    for index, section in enumerate(sections):
        title, _, pending = section.partition('\n')
        if re.fullmatch(r'## \[?unreleased\]?\s*', title, flags=re.I):
            if pending.strip():
                carried.append(pending.strip())
            sections[index] = f'{title}\n\n'
    # Above the newest release, and below an Unreleased heading that leads the file.
    at = next((index for index, section in enumerate(sections)
               if not re.match(r'## \[?unreleased\]?\s*$', section, flags=re.I | re.M)),
              len(sections))
    entries = '\n'.join([f'- {note}', *carried])
    sections.insert(at, f'## {version} - {date}\n\n{entries}\n\n')
    if not (head + ''.join(sections[:at])).endswith('\n\n'):
        sections[at] = '\n' + sections[at]
    return head + ''.join(sections)


def release(repo, plugin, name, version, notes):
    """Write the version everywhere it is recorded, and the changelog."""
    rewrite_json(plugin / '.claude-plugin/plugin.json', lambda data: data.update(version=version))

    def in_marketplace(data):
        next(entry for entry in data['plugins'] if entry['name'] == name)['version'] = version
    rewrite_json(repo / '.claude-plugin/marketplace.json', in_marketplace)
    (plugin / 'CHANGELOG.md').write_text(notes, encoding='utf-8')


def listing(title, items, empty):
    lines = [f'### {title}', '']
    lines += [f'- `{item}`' for item in items] or [f'- {empty}']
    return lines + ['']


def body(old, new, report, version):
    """The pull request description, in the language this repository's PRs use."""
    repository = new['repository']
    root = new['upstream_root']
    lines = [
        '## Summary',
        '',
        f"`{root}`가 원문 저장소에서 바뀌어 다시 들여왔습니다. 자동 병합은 하지 않습니다.",
        '',
        f"- 기준 커밋: `{old['commit'][:7]}` → `{new['commit'][:7]}`",
        f"- 원문 버전: {old.get('version', '?')} → {new.get('version', '?')}",
        f'- 플러그인 버전: {version}',
        f"- 원문 변경 내역: {repository}/compare/{old['commit']}...{new['commit']}",
        '',
        '## 병합 전에 할 일',
        '',
        '1. 이 PR의 `validate` 실행이 승인 대기 중이면 "Approve workflows to run"을 누릅니다.',
        '2. 아래 "분류되지 않은 새 원문 파일"을 잠금 파일에 분류합니다. 들일 파일은 '
        '`sync --accept-new`로, 들이지 않을 파일은 `skip`에 경로를 더한 뒤 `sync`로 처리합니다.',
        '3. "원문에서 지워진 파일"은 이 저장소에서도 지우거나 잠금 파일에서 `local`로 바꿉니다.',
        '4. "충돌이 남은 파일"의 충돌 표시를 풀고 `import_upstream.py patch`로 다시 기록합니다.',
        '',
    ]
    lines += listing('분류되지 않은 새 원문 파일', report['unclassified'], '없음')
    lines += listing('원문에서 지워진 파일', report['removed'], '없음')
    lines += listing('충돌이 남은 파일', report['conflicts'], '없음')
    lines += listing('사람이 고쳐 둔 파일 (`patched`)', report['patched'], '없음')
    lines += listing('내용이 바뀐 원문 파일', report['updated'], '없음')
    lines += listing('잠금 파일에 새로 적은 원문 파일', report['new'], '없음')
    return '\n'.join(lines)


def prepare(repo, plugin, source, date):
    old = import_upstream.read_lock(plugin)
    if not import_upstream.upstream_changed(old, source):
        return None
    name, version, notes = planned_release(repo, plugin)
    report = import_upstream.sync(plugin, source)
    new = import_upstream.read_lock(plugin)
    note = (f"Sync with `{new['repository'].removeprefix('https://github.com/')}` at "
            f"`{new['commit'][:7]}` (upstream version {new.get('version', 'unknown')}).")
    release(repo, plugin, name, version, with_release(notes, version, date, note))
    return body(old, new, report, version)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--plugin', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path,
                        help="upstream checkout at the new commit that also has the lock's commit")
    parser.add_argument('--date', required=True, help='release date, YYYY-MM-DD')
    parser.add_argument('--body-file', required=True, type=Path)
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    text = prepare(repo, args.plugin, args.source, args.date)
    if text is None:
        print('upstream did not change under the imported folder')
        return UNCHANGED
    args.body_file.write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
