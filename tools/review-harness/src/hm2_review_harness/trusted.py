"""Resolve one release's bundled skills, never a target PR's instructions."""
import hashlib
import importlib.util
import json
from pathlib import Path

from .state import HarnessError


def bundle_root():
    packaged = Path(__file__).parent / 'bundle'
    if packaged.is_dir():
        manifest = json.loads((packaged / 'manifest.json').read_text())
        for name, expected in manifest['files'].items():
            path = packaged / name
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise HarnessError('Bundled skill differs from its release manifest: ' + name)
        return packaged
    checkout = Path(__file__).resolve().parents[4] / 'plugins'
    if not (checkout / 'review/skills/review-code/scripts/automation_contract.py').is_file():
        raise HarnessError('Incomplete installation: bundled review skills are missing')
    return checkout


def module(skill, script):
    path = bundle_root() / 'review/skills' / skill / 'scripts' / script
    spec = importlib.util.spec_from_file_location('hm2_' + path.stem, path)
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    return loaded


def instructions(scenario):
    root = bundle_root()
    selected = {'S1': ['review-code'], 'S2': ['review-respond', 'review-check', 'review-code'],
                'S3': ['review-pr', 'review-code'], 'S4': ['review-pr', 'review-check', 'review-code']}[scenario]
    result = {}
    for skill in selected:
        base = root / 'review/skills' / skill
        for path in sorted(base.rglob('*.md')):
            if 'evals' not in path.relative_to(base).parts:
                result[str(path.relative_to(root))] = path.read_text()
    content = root / 'content/skills/un-ai'
    if content.is_dir():
        for path in sorted(content.rglob('*.md')):
            if 'evals' not in path.relative_to(content).parts:
                result[str(path.relative_to(root))] = path.read_text()
    return result
