"""Prepare disposable Git sources without activating incoming hooks or filters."""
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import subprocess

from .state import HarnessError


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0',
               GIT_NO_LAZY_FETCH='1', GIT_LFS_SKIP_SMUDGE='1')
    return env


def git(root, *args, data=None, executable='git'):
    command = [executable, '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=' + os.devnull,
               '-c', 'core.attributesFile=' + os.devnull, '-c', 'protocol.file.allow=always', '-C', str(root), *args]
    value = subprocess.run(command, input=data, capture_output=True, timeout=180, env=environment())
    if value.returncode:
        raise HarnessError('Git preparation failed: ' + value.stderr.decode(errors='replace').strip())
    return value.stdout


def init(root, executable='git'):
    root = Path(root); root.mkdir(parents=True)
    subprocess.run([executable, '-c', 'init.templateDir=', 'init', '-q', str(root)],
                   env=environment(), check=True, capture_output=True)
    git(root, 'config', 'core.hooksPath', os.devnull, executable=executable)


def pr_checkout(config, event, snapshot, root):
    executable = config['git_path']; init(root, executable)
    url = f'https://{event["hostname"]}/{event["repo"]}.git'
    helper = '!' + shlex.quote(config['gh_path']) + ' auth git-credential'
    # Fetch immutable commits and the actual PR ref. No submodules or setup code run.
    git(root, '-c', 'credential.helper=', '-c', 'credential.helper=' + helper, 'fetch', '--no-tags', url,
        f'refs/pull/{event["pr"]}/head', snapshot['pr']['base']['sha'], executable=executable)
    head = snapshot['pr']['head']['sha']
    git(root, 'cat-file', '-e', head + '^{commit}', executable=executable)
    git(root, '-c', 'filter.lfs.process=', '-c', 'filter.lfs.smudge=', '-c', 'filter.lfs.required=false',
        'checkout', '-q', '--detach', '--no-recurse-submodules', head, executable=executable)
    return Path(root)


def safe_path(root, relative):
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or not parts.parts or '\x00' in relative:
        raise HarnessError('Unsupported source path')
    path = Path(root)
    for part in parts.parts[:-1]:
        path /= part
        if path.is_symlink():
            raise HarnessError('Source path traverses a symlink')
    return Path(root) / relative


def local_checkout(config, original, root, gate):
    original = Path(original).resolve()
    before = gate.capture_scope(original, working_tree=True)
    executable = config['git_path']; init(root, executable)
    git(root, 'fetch', '--no-tags', str(original), before['target']['head_sha'], executable=executable)
    git(root, 'checkout', '-q', '--detach', '--no-recurse-submodules', before['target']['head_sha'], executable=executable)
    entries = git(original, 'ls-files', '--stage', '-z', executable=executable)
    for entry in entries.split(b'\x00'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1); mode, oid, stage = meta.split()
        if stage != b'0':
            raise HarnessError('Unmerged index cannot be snapshotted')
        if mode != b'160000':
            raw = git(original, 'cat-file', 'blob', oid.decode(), executable=executable)
            copied = git(root, 'hash-object', '-w', '--stdin', data=raw, executable=executable).strip()
            if copied != oid:
                raise HarnessError('Staged object changed during snapshot')
    git(root, 'read-tree', '--empty', executable=executable)
    git(root, 'update-index', '-z', '--index-info', data=entries, executable=executable)
    names = set(git(original, 'ls-files', '-z', executable=executable).decode().split('\x00'))
    names.update(git(original, 'ls-files', '--others', '--exclude-standard', '-z', executable=executable).decode().split('\x00'))
    names.update(git(root, 'ls-tree', '-r', '--name-only', '-z', 'HEAD', executable=executable).decode().split('\x00'))
    for name in sorted(names - {''}):
        source, target = safe_path(original, name), safe_path(root, name)
        if source.is_dir() and not source.is_symlink():
            continue  # Gitlink handling remains explicit in the scope gate.
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                raise HarnessError('Cannot replace a directory in a local snapshot')
            target.unlink()
        if not source.exists() and not source.is_symlink():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
                target.write_bytes(stream.read())
            target.chmod(stat.S_IMODE(source.stat().st_mode))
    after = gate.capture_scope(original, working_tree=True)
    copied = gate.capture_scope(root, working_tree=True)
    if before != after or before['target'] != copied['target']:
        raise HarnessError('Local source changed or snapshot is not equivalent; collect again')
    return Path(root), copied


def packet(root, scope, max_bytes, previous_head=None):
    """Send text only. Omitted/binary source is an explicit review limitation."""
    paths = git(root, 'ls-tree', '-r', '--name-only', '-z', scope['target']['head_sha']).decode().split('\x00')
    changed = [row['path'] for row in scope['files']]
    order = list(dict.fromkeys(changed + [p for p in paths if p]))
    sources, omitted, used = {}, [], 0
    for revision in ('head', 'base', 'index', 'working'):
        if scope['target']['mode'] != 'working-tree' and revision in ('index', 'working'):
            continue
        for name in order:
            if revision == 'base' and name not in changed and PurePosixPath(name).name not in ('AGENTS.md', 'CLAUDE.md'):
                continue
            try:
                if revision == 'working':
                    path = safe_path(root, name)
                    if path.is_symlink() or not path.is_file():
                        continue
                    raw = path.read_bytes()
                else:
                    ref = ':' + name if revision == 'index' else scope['target'][revision + '_sha'] + ':' + name
                    raw = git(root, 'show', ref)
                text = raw.decode('utf-8')
                if '\x00' in text or used + len(raw) > max_bytes:
                    omitted.append(revision + ':' + name); continue
                sources[revision + ':' + name] = text; used += len(raw)
            except (HarnessError, UnicodeError):
                # Deleted/untracked paths may not exist at all revisions.
                if revision == 'working' or (revision == 'head' and scope['target']['mode'] == 'commits'):
                    omitted.append(revision + ':' + name)
    delta = None
    if previous_head:
        try:
            delta = git(root, 'diff', '--no-ext-diff', '--no-textconv', previous_head, scope['target']['head_sha'], '--').decode()
            if len(delta.encode()) > max_bytes:
                delta = None; omitted.append('previous-review delta exceeds packet limit')
        except HarnessError:
            omitted.append('previous-review objects unavailable; full current PR scope is supplied')
    rules = {name: value for name, value in sources.items()
             if name.startswith('base:') and PurePosixPath(name.split(':', 1)[1]).name in ('AGENTS.md', 'CLAUDE.md')}
    return {'sources': sources, 'repository_paths': paths, 'trusted_base_rules': rules,
            'previous_review_delta': delta, 'omitted': omitted}
