"""Read a plugin's `upstream.lock.json`, the record of files imported from another repository.

A plugin that carries upstream skills verbatim cannot follow this repository's
authoring rules without diverging from its source. The lock names exactly which
files are imported, so the tests relax a rule for those paths and nowhere else.

Shape the tests rely on:

    {"upstream_root": "harness/pstack/claude-code",
     "files": [{"upstream": "harness/pstack/claude-code/skills/arena/SKILL.md",
                "path": "skills/arena/SKILL.md", "status": "verbatim"},
               {"upstream": "harness/pstack/claude-code/skills/statechart/SKILL.md",
                "status": "skipped"}]}

`upstream` is the path in the source repository. `upstream_root` is the folder
there that corresponds to the plugin folder. `path` is relative to the plugin
folder; a skipped file has none.
"""
import json
from pathlib import PurePosixPath

LOCK_NAME = 'upstream.lock.json'
# The file's content comes from upstream: unchanged, with a generated line
# inserted, or with a reviewed local patch.
IMPORTED = ('verbatim', 'injected', 'patched')
STATUSES = (*IMPORTED, 'skipped', 'local')


def read(plugin):
    """Return the lock, or None when the plugin imports nothing."""
    path = plugin / LOCK_NAME
    if not path.is_file():
        return None
    lock = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(lock.get('upstream_root', ''), str):
        raise ValueError(f'{path}: upstream_root is not a string')
    for entry in lock['files']:
        if entry.get('status') not in STATUSES:
            raise ValueError(f'{path}: unknown status in {entry!r}')
    return lock


def load(plugin):
    """Return the lock's file entries, or None when the plugin imports nothing."""
    lock = read(plugin)
    return None if lock is None else lock['files']


def imported_files(plugin):
    """Plugin-relative paths whose content the lock records as imported."""
    return {
        PurePosixPath(entry['path']).as_posix()
        for entry in load(plugin) or []
        if entry['status'] in IMPORTED and entry.get('path')
    }


def imported_skills(plugin):
    """Skill folders whose SKILL.md the lock records as imported."""
    skills = set()
    for path in imported_files(plugin):
        parts = PurePosixPath(path).parts
        if len(parts) == 3 and parts[0] == 'skills' and parts[2] == 'SKILL.md':
            skills.add(parts[1])
    return skills


def skipped_files(plugin):
    """Where each deliberately skipped upstream file would sit in the plugin.

    A skipped entry outside `upstream_root` has no place in the plugin and is
    left out, as is one that walks out of the root with `..`.
    """
    lock = read(plugin) or {'files': []}
    root = PurePosixPath(lock.get('upstream_root', '')).parts
    places = set()
    for entry in lock['files']:
        parts = PurePosixPath(entry.get('upstream') or '').parts
        if entry['status'] != 'skipped' or parts[:len(root)] != root or '..' in parts:
            continue
        if len(parts) > len(root):
            places.add(PurePosixPath(*parts[len(root):]).as_posix())
    return places
