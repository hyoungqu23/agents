"""Print the plugins the Codex marketplace lists, one name per line.

validate.sh asks this to decide which plugins owe a Codex manifest. A plugin
that Codex cannot load, such as one whose skills are all hidden from the model,
is published for Claude Code only by leaving it out of that marketplace.
"""
import json
import posixpath
import sys


def listed_plugins(marketplace):
    names = []
    for plugin in marketplace.get('plugins', []):
        name = plugin.get('name') if isinstance(plugin, dict) else None
        if not isinstance(name, str) or not name:
            raise SystemExit(f'Codex marketplace entry has no name: {plugin!r}')
        # validate.sh pairs a name with plugins/<name>, so a local source that
        # points elsewhere would be checked against the wrong folder.
        source = plugin.get('source')
        if isinstance(source, dict) and source.get('source') == 'local':
            if posixpath.normpath(str(source.get('path'))) != f'plugins/{name}':
                raise SystemExit(f'Codex marketplace entry {name} does not point at plugins/{name}')
        names.append(name)
    return names


def main():
    with open(sys.argv[1], encoding='utf-8') as handle:
        print('\n'.join(listed_plugins(json.load(handle))))


if __name__ == '__main__':
    main()
