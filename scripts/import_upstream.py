"""Import a plugin's files from a checkout of its upstream repository.

A plugin that carries another repository's files records them in
`upstream.lock.json`. The lock's header says where the files come from and how
they are placed; its `files` list says what happened to each upstream file.

    sync   copy the upstream files named by the lock from a checkout, re-insert
           the generated line, merge upstream changes into patched files, and
           rewrite the lock
    check  compare the lock with the plugin folder, and with a checkout when
           one is given or fetched
    patch  record a hand-edited imported file as patched

Header fields this script reads:

    commit         the upstream commit the files were taken from
    upstream_root  the upstream folder that corresponds to the plugin folder
    skip           path prefixes under that folder that are not imported
    relocate       path prefixes under that folder and where they go instead
    inject         {"after": line, "line": line}: every imported file that has
                   the first line gets the second one as the next paragraph
    version_file   a JSON file under that folder whose `version` is copied to
                   the lock's `version`

Hashes are git blob ids, so they can be compared with `git ls-tree` output or
the GitHub tree API without downloading a file. Upstream content, the file list
and the executable bit are read from the checkout's HEAD commit, never from its
working tree, so the commit in the lock reproduces the result.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

LOCK_NAME = 'upstream.lock.json'
IMPORTED = ('verbatim', 'injected', 'patched')
CONFLICT_MARKERS = (b'<<<<<<< ', b'>>>>>>> ')


def blob_id(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def read_lock(plugin):
    return json.loads((plugin / LOCK_NAME).read_text(encoding='utf-8'))


def write_lock(plugin, lock):
    lock['files'].sort(key=lambda entry: entry.get('upstream') or f"~{entry.get('path')}")
    text = json.dumps(lock, indent=2, ensure_ascii=False) + '\n'
    (plugin / LOCK_NAME).write_text(text, encoding='utf-8')


def under(path, prefix):
    """Whether path is prefix itself or inside the folder a trailing slash names."""
    return path.startswith(prefix) if prefix.endswith('/') else path == prefix


def placed(lock, relative):
    """Where an upstream file under the root sits in the plugin."""
    for prefix, target in lock.get('relocate', {}).items():
        if under(relative, prefix):
            return target + relative[len(prefix):]
    return relative


def injected(lock, data):
    """The file's content with the generated line inserted, or None when it has no anchor."""
    rule = lock.get('inject')
    if not rule:
        return None
    lines = data.decode('utf-8', errors='surrogateescape').split('\n')
    if rule['after'] not in lines:
        return None
    index = lines.index(rule['after'])
    lines[index + 1:index + 1] = ['', rule['line']]
    return '\n'.join(lines).encode('utf-8', errors='surrogateescape')


def without_injection(lock, data):
    """Undo `injected`: the upstream content, or None when the line is not where sync puts it."""
    rule = lock.get('inject')
    if not rule:
        return None
    lines = data.decode('utf-8', errors='surrogateescape').split('\n')
    if rule['after'] not in lines:
        return None
    index = lines.index(rule['after'])
    if lines[index + 1:index + 3] != ['', rule['line']]:
        return None
    del lines[index + 1:index + 3]
    return '\n'.join(lines).encode('utf-8', errors='surrogateescape')


def git_output(source, *args):
    return subprocess.run(
        ['git', '-C', str(source), *args], check=True, capture_output=True).stdout


def upstream_files(source, commit, root):
    """Map each file under root in the commit to (blob id, executable)."""
    listed = git_output(source, 'ls-tree', '-r', '-z', commit, '--', root).decode('utf-8')
    files = {}
    for record in filter(None, listed.split('\0')):
        meta, path = record.split('\t', 1)
        mode, kind, blob = meta.split()
        if kind == 'blob' and mode != '120000':
            files[path] = (blob, mode == '100755')
    return files


def checked_out_commit(source):
    return git_output(source, 'rev-parse', 'HEAD').decode().strip()


def is_executable(path):
    return bool(path.stat().st_mode & 0o100)


def upstream_changed(lock, source):
    """Whether the checkout's HEAD differs from the lock's commit under the root."""
    root = lock['upstream_root'].rstrip('/')
    old, new = (git_output(source, 'rev-parse', f'{commit}:{root}').strip()
                for commit in (lock['commit'], 'HEAD'))
    return old != new


def merged(plugin, source, lock, entry, new):
    """Merge upstream's change into a patched file. Returns (content, conflicted)."""
    try:
        old = git_output(source, 'cat-file', 'blob', entry['upstream_blob'])
    except subprocess.CalledProcessError:
        raise SystemExit(
            f"{entry['path']}: the checkout lacks the old upstream content "
            f"{entry['upstream_blob']}; fetch the lock's commit {lock['commit']} into it")
    with tempfile.TemporaryDirectory() as directory:
        names = []
        # The patch was made on the injected text, so both upstream sides get
        # the generated line before they are compared with it.
        for label, data in (('ours', (plugin / entry['path']).read_bytes()),
                            ('base', injected(lock, old) or old),
                            ('theirs', injected(lock, new) or new)):
            names.append(str(Path(directory) / label))
            Path(names[-1]).write_bytes(data)
        result = subprocess.run(
            ['git', 'merge-file', '-p', '-L', 'this repository', '-L', 'old upstream',
             '-L', 'new upstream', *names], capture_output=True)
    if result.returncode < 0 or result.returncode > 127:
        raise SystemExit(f"{entry['path']}: merge failed: {result.stderr.decode()}")
    return result.stdout, result.returncode > 0


def sync(plugin, source, accept_new=False):
    """Bring the plugin to the checkout's commit. Returns a report dict."""
    lock = read_lock(plugin)
    root = lock['upstream_root'].rstrip('/') + '/'
    known = {entry['upstream']: entry for entry in lock['files'] if entry.get('upstream')}

    report = {'updated': [], 'new': [], 'removed': [], 'unclassified': [],
              'patched': [], 'conflicts': []}
    # Resolved once: the checkout may move while this runs, and the lock must
    # name the commit the files were read from.
    commit = checked_out_commit(source)
    files = upstream_files(source, commit, root.rstrip('/'))
    version = lock.get('version')
    if lock.get('version_file'):
        # Read before anything is written, so a bad manifest changes nothing.
        try:
            manifest = git_output(source, 'show', f"{commit}:{root}{lock['version_file']}")
            version = json.loads(manifest)['version']
        except (subprocess.CalledProcessError, ValueError, KeyError, TypeError):
            raise SystemExit(
                f"nothing was written: {root}{lock['version_file']} has no readable version")
    entries = [entry for entry in lock['files'] if not entry.get('upstream')]
    refused = []
    writes = []
    for upstream, (blob, executable) in sorted(files.items()):
        relative = upstream[len(root):]
        entry = known.get(upstream)
        if entry is None:
            if any(under(relative, prefix) for prefix in lock.get('skip', [])):
                entry = {'upstream': upstream, 'status': 'skipped'}
            elif accept_new:
                entry = {'upstream': upstream, 'status': 'verbatim'}
            else:
                report['unclassified'].append(upstream)
                continue
            report['new'].append(upstream)
        elif entry.get('upstream_blob') != blob:
            report['updated'].append(upstream)

        if entry['status'] == 'patched':
            report['patched'].append(entry['path'])
            target = plugin / entry['path']
            # Content and the executable bit change independently upstream.
            if entry.get('upstream_blob') != blob or bool(entry.get('executable')) != executable:
                if (not target.is_file() or target.is_symlink()
                        or blob_id(target.read_bytes()) != entry.get('applied_blob')):
                    # Merging would fold an edit nobody recorded into the patch.
                    refused.append(
                        f"{entry['path']}: differs from the recorded patch; "
                        'restore it or record it with `patch` first')
                    entries.append(entry)
                    continue
                content, conflicted = target.read_bytes(), False
                if entry.get('upstream_blob') != blob:
                    content, conflicted = merged(
                        plugin, source, lock, entry, git_output(source, 'cat-file', 'blob', blob))
                if conflicted:
                    report['conflicts'].append(entry['path'])
                entry = {**entry, 'upstream_blob': blob, 'applied_blob': blob_id(content)}
                entry.pop('executable', None)
                if executable:
                    entry['executable'] = True
                writes.append((entry['path'], content, executable, upstream))
            entries.append(entry)
            continue

        entry = {'upstream': upstream, 'status': entry['status'], 'upstream_blob': blob}
        if entry['status'] != 'skipped':
            entry['path'] = placed(lock, relative)
            data = git_output(source, 'cat-file', 'blob', blob)
            content = injected(lock, data)
            entry['status'] = 'verbatim' if content is None else 'injected'
            if content is not None:
                entry['applied_blob'] = blob_id(content)
            if executable:
                entry['executable'] = True
            writes.append(
                (entry['path'], data if content is None else content, executable, upstream))
        entries.append(entry)

    # Nothing is written until every destination is known to be safe: one
    # upstream file must not replace another, a file written here, or anything
    # outside the plugin folder. A destination belongs to the upstream file the
    # lock already places there, including one that is kept without a write.
    owner = {entry['path']: upstream for upstream, entry in known.items() if entry.get('path')}
    local = {entry['path'] for entry in entries if not entry.get('upstream')}
    seen = set()
    for path, _, _, upstream in writes:
        parts = PurePosixPath(path).parts
        target = plugin / path
        if PurePosixPath(path).is_absolute() or '..' in parts or not parts:
            refused.append(f'{path}: leaves the plugin folder')
        elif path in seen:
            refused.append(f'{path}: two upstream files are placed here')
        elif path in local or path == LOCK_NAME:
            refused.append(f'{path}: is a file written in this repository')
        elif owner.get(path, upstream) != upstream:
            refused.append(f'{path}: already holds the upstream file {owner[path]}')
        elif path not in owner and (target.exists() or target.is_symlink()):
            refused.append(f'{path}: exists but the lock does not list it as imported')
        elif target.is_dir() and not target.is_symlink():
            refused.append(f'{path}: is a folder here; remove it first')
        else:
            # A file upstream turned into a folder leaves the old file in the way.
            for parent in list(target.relative_to(plugin).parents)[:-1]:
                blocker = plugin / parent
                if blocker.is_symlink() or (blocker.exists() and not blocker.is_dir()):
                    refused.append(
                        f'{path}: {parent.as_posix()} is a file here; remove it first')
        seen.add(path)
    if refused:
        raise SystemExit('nothing was written:\n' + '\n'.join(refused))

    for path, content, executable, _ in writes:
        target = plugin / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o755 if executable else 0o644)

    for upstream, entry in sorted(known.items()):
        if upstream not in files and entry['status'] == 'skipped':
            # Nothing of it is here, so there is nothing for a person to decide.
            continue
        if upstream not in files:
            # Deleting here would hide the removal; a person deletes the file
            # or marks it local, and `check --source` fails until then.
            report['removed'].append(upstream)
            entries.append(entry)

    lock['files'] = entries
    lock['commit'] = commit
    if version is not None:
        lock['version'] = version
    write_lock(plugin, lock)
    return report


def mark_patched(plugin, path):
    """Record the file's current content as a reviewed patch of its upstream file."""
    lock = read_lock(plugin)
    for entry in lock['files']:
        if entry.get('path') == path and entry.get('status') in IMPORTED:
            entry['status'] = 'patched'
            entry['applied_blob'] = blob_id((plugin / path).read_bytes())
            write_lock(plugin, lock)
            return
    raise SystemExit(f'{path}: not an imported file in {LOCK_NAME}')


def fetched(lock, directory):
    """Fetch the lock's commit into directory, without file contents, and check it out."""
    directory.mkdir(parents=True, exist_ok=True)
    git_output(directory, 'init', '-q')
    git_output(directory, 'fetch', '-q', '--depth', '1', '--filter=blob:none',
               lock['repository'], lock['commit'])
    # `check` reads tree entries only, so nothing is checked out.
    git_output(directory, 'update-ref', '--no-deref', 'HEAD', 'FETCH_HEAD')
    return directory


def check(plugin, source=None):
    """List what disagrees between the lock, the plugin folder and a checkout."""
    lock = read_lock(plugin)
    problems = []
    listed = set()
    for entry in lock['files']:
        status, path = entry.get('status'), entry.get('path')
        name = path or entry.get('upstream')
        if status == 'skipped':
            if path:
                problems.append(f'{name}: a skipped file has no path')
            continue
        if status not in (*IMPORTED, 'local') or not path:
            problems.append(f'{name}: needs a path and a known status')
            continue
        if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
            problems.append(f'{path}: leaves the plugin folder')
            continue
        if path in listed:
            problems.append(f'{path}: listed twice')
        listed.add(path)
        target = plugin / path
        if not target.is_file() or target.is_symlink():
            problems.append(f'{path}: listed as {status} but is not a regular file')
            continue
        if status == 'local':
            if entry.get('upstream'):
                problems.append(f'{path}: a local file has no upstream path')
            continue
        data = target.read_bytes()
        if any(line.startswith(CONFLICT_MARKERS) for line in data.split(b'\n')):
            problems.append(f'{path}: has a merge conflict marker')
        key = 'upstream_blob' if status == 'verbatim' else 'applied_blob'
        if entry.get(key) != blob_id(data):
            problems.append(f'{path}: content does not match {key}')
        if status == 'verbatim' and injected(lock, data) is not None:
            problems.append(f'{path}: has the anchor line, so sync would insert the generated line')
        if status == 'injected':
            # The hash alone cannot vouch for an injected file: whoever edits
            # the file can update applied_blob. Taking the generated line back
            # out must give exactly the upstream content.
            original = without_injection(lock, data)
            if original is None:
                problems.append(f'{path}: the generated line does not follow the anchor line')
            elif blob_id(original) != entry.get('upstream_blob'):
                problems.append(f'{path}: differs from upstream by more than the generated line')
        if is_executable(target) != bool(entry.get('executable')):
            problems.append(f'{path}: executable bit does not match the lock')

    for found in sorted(plugin.rglob('*')):
        relative = found.relative_to(plugin).as_posix()
        if found.is_file() and relative != LOCK_NAME and relative not in listed:
            problems.append(f'{relative}: not listed in {LOCK_NAME}')

    if source is not None:
        problems += compare_with_source(lock, source)
    return problems


def compare_with_source(lock, source):
    problems = []
    if checked_out_commit(source) != lock['commit']:
        return [f"checkout is not at the lock's commit {lock['commit']}"]
    root = lock['upstream_root'].rstrip('/')
    files = upstream_files(source, lock['commit'], root)
    known = {entry['upstream']: entry for entry in lock['files'] if entry.get('upstream')}
    for upstream in sorted(files.keys() - known.keys()):
        problems.append(f'{upstream}: upstream file is not classified in the lock')
    for upstream in sorted(known.keys() - files.keys()):
        problems.append(f'{upstream}: listed but absent upstream; delete it or mark it local')
    for upstream in sorted(files.keys() & known.keys()):
        blob, executable = files[upstream]
        entry = known[upstream]
        if entry.get('upstream_blob') != blob:
            problems.append(f'{upstream}: upstream_blob does not match upstream')
        if entry['status'] != 'skipped' and bool(entry.get('executable')) != executable:
            problems.append(f'{upstream}: executable bit does not match upstream')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('sync', 'check', 'patch'):
        command = commands.add_parser(name)
        command.add_argument('--plugin', required=True, type=Path)
    for name in ('sync', 'check'):
        commands.choices[name].add_argument(
            '--source', type=Path, required=name == 'sync',
            help='checkout of the upstream repository')
    commands.choices['check'].add_argument(
        '--fetch', type=Path, metavar='DIR',
        help="fetch the lock's commit into DIR and compare with it")
    commands.choices['patch'].add_argument(
        '--path', required=True, help='imported file, relative to the plugin folder')
    commands.choices['sync'].add_argument(
        '--accept-new', action='store_true',
        help='import upstream files the lock does not classify, instead of reporting them')
    args = parser.parse_args(argv)

    if args.command == 'sync':
        report = sync(args.plugin, args.source, args.accept_new)
        json.dump(report, sys.stdout, indent=2)
        print()
        return 0
    if args.command == 'patch':
        mark_patched(args.plugin, args.path)
        return 0
    source = args.source
    if args.fetch:
        source = fetched(read_lock(args.plugin), args.fetch)
    problems = check(args.plugin, source)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
