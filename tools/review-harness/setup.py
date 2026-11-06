"""Build one release from canonical plugin sources, with no installed-cache dependency."""
import hashlib
import json
from pathlib import Path
import shutil

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

ROOT = Path(__file__).parent.resolve()


def copy_bundle(destination):
    staged = ROOT / 'bundled'
    if staged.is_dir():
        shutil.copytree(staged, destination, dirs_exist_ok=True)
        return
    plugins = ROOT.parents[1] / 'plugins'
    paths = [plugins / 'review/skills', plugins / 'content/skills/un-ai']
    if not all(path.is_dir() for path in paths):
        raise RuntimeError('Build requires canonical monorepo skills or the release sdist bundle')
    files = {}
    for base in paths:
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(plugins)
            if (not path.is_file() or path.is_symlink() or any(part in ('evals', '__pycache__') for part in relative.parts)
                    or path.suffix not in ('.md', '.py', '.json', '.yaml')):
                continue
            target = destination / relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            files[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    destination.mkdir(parents=True, exist_ok=True)
    version = json.loads((plugins / 'review/.codex-plugin/plugin.json').read_text())['version']
    (destination / 'manifest.json').write_text(json.dumps({'schema_version': 1, 'review_version': version, 'files': files}, sort_keys=True, indent=2) + '\n')


class Build(build_py):
    def run(self):
        super().run()
        copy_bundle(Path(self.build_lib) / 'hm2_review_harness/bundle')


class Source(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        copy_bundle(Path(base_dir) / 'bundled')


setup(packages=find_packages('src'), package_dir={'': 'src'}, cmdclass={'build_py': Build, 'sdist': Source})
