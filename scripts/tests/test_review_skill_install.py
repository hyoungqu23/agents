"""Skill references must survive copying just a plugin's skill directories."""
from pathlib import Path
import json
import re
import shutil
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

# Lets `python3 -m unittest scripts/tests/<this file>` find the sibling module,
# which only `discover -s scripts/tests` puts on the path by itself.
sys.path.insert(0, str(Path(__file__).parent))
import upstream_lock  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOTS = sorted((ROOT / 'plugins').glob('*/skills'))
# Template links that resolve only after the template is saved as the real
# SPEC.md and QUESTIONS.md, which sit beside each other in the target project.
TEMPLATE_LINKS = {
    'spec/assets/SPEC.template.md -> ./QUESTIONS.md',
    'spec/assets/QUESTIONS.template.md -> ./SPEC.md',
}


def broken_links(root, documents=None, upstream_gaps=None):
    """List links in the Markdown under documents that leave root or miss a file.

    root is the installed folder a link may not leave. documents is the folder
    whose Markdown is checked; it defaults to root. A link that ends in a slash
    names a folder and needs that folder. upstream_gaps is a pair of path sets
    relative to root: files imported from upstream, and files the import left
    out on purpose. Text carried verbatim still links what was left out, so a
    missing target is allowed only from the first set to the second.
    """
    documents = documents or root
    imported, skipped = upstream_gaps or (set(), set())
    resolved = root.resolve()
    failures = []
    for source in sorted(documents.rglob('*.md')):
        if 'evals' in source.relative_to(documents).parts:
            continue
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', source.read_text()):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (source.parent / unquote(url.path)).resolve()
            present = target.is_dir() if url.path.endswith('/') else target.is_file()
            if not target.is_relative_to(resolved):
                present = False
            elif (not target.exists()
                  and source.relative_to(root).as_posix() in imported
                  and target.relative_to(resolved).as_posix() in skipped):
                continue
            if not present:
                failures.append(f'{source.relative_to(documents)} -> {link}')
    return failures


class ReviewSkillInstallTests(unittest.TestCase):
    def test_references_survive_skill_directory_install(self):
        # A plugin with an upstream lock keeps upstream's layout, where skills link
        # the plugin's docs folder, and so supports plugin installation only.
        roots = [root for root in SKILL_ROOTS if upstream_lock.load(root.parent) is None]
        skills = [path for root in roots for path in root.glob('*/SKILL.md')]
        self.assertEqual(len(skills), 18)
        excluded = set()
        for skill_root in roots:
            plugin = skill_root.parent.name
            with self.subTest(plugin=plugin), tempfile.TemporaryDirectory() as temporary:
                installed = Path(temporary) / '.agents/skills'
                shutil.copytree(skill_root, installed)
                broken = set(broken_links(installed))
                if plugin == 'product':
                    excluded = broken & TEMPLATE_LINKS
                    broken -= TEMPLATE_LINKS
                self.assertEqual(sorted(broken), [])
        self.assertEqual(excluded, TEMPLATE_LINKS)

    def test_references_survive_plugin_install(self):
        for skill_root in SKILL_ROOTS:
            with self.subTest(plugin=skill_root.parent.name), tempfile.TemporaryDirectory() as temporary:
                installed = Path(temporary) / skill_root.parent.name
                shutil.copytree(skill_root.parent, installed)
                broken = set(broken_links(
                    installed, installed / 'skills',
                    (upstream_lock.imported_files(skill_root.parent),
                     upstream_lock.skipped_files(skill_root.parent))))
                self.assertEqual(sorted(broken - TEMPLATE_LINKS), [])

    def test_copied_shared_references_match_plugin_originals(self):
        copies = 0
        for skill_root in SKILL_ROOTS:
            shared = skill_root.parent / 'references'
            for reference in sorted(skill_root.glob('*/references/*.md')):
                canonical = shared / reference.name
                if not canonical.is_file():
                    continue
                copies += 1
                with self.subTest(reference=str(reference.relative_to(ROOT))):
                    self.assertEqual(reference.read_bytes(), canonical.read_bytes())
        self.assertTrue(copies)

    def test_evaluation_inputs_stay_outside_distributed_skills(self):
        for plugin, skill in (('review', 'review-code'), ('review', 'review-pr'), ('product', 'prd-gate')):
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as temp:
                installed = Path(temp) / 'skills'
                shutil.copytree(ROOT / 'plugins' / plugin / 'skills', installed)
                self.assertTrue((installed / skill / 'SKILL.md').is_file())
                self.assertFalse((installed / skill / 'evals').exists())
                if skill == 'prd-gate':
                    self.assertEqual(broken_links(installed / skill), [])
                    for reference in (installed / skill / 'references').glob('*.md'):
                        canonical = ROOT / 'plugins/product/references' / reference.name
                        self.assertEqual(reference.read_bytes(), canonical.read_bytes())
                suite = ROOT / 'evals' / plugin / skill
                for case in json.loads((suite / 'evals.json').read_text())['evals']:
                    for name in case['files']:
                        self.assertTrue((suite / name).is_file(), name)

    def test_reference_checker_rejects_missing_and_outside_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'skills'
            root.mkdir()
            (root.parent / 'outside.md').write_text('Not installed')
            (root / 'SKILL.md').write_text(
                '[missing](missing.md) [outside](../outside.md) '
                '[web](https://example.invalid/doc) [anchor](#heading)')
            self.assertEqual(len(broken_links(root)), 2)

    def test_reference_checker_accepts_plugin_references_only_inside_plugin(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / 'plugin'
            skills = plugin / 'skills'
            (skills / 'demo').mkdir(parents=True)
            (plugin / 'references').mkdir()
            shared = plugin / 'references/shared.md'
            shared.write_text('Shared')
            (plugin / 'README.md').write_text('[not a skill document](missing.md)')
            (skills / 'demo/SKILL.md').write_text('[shared](../../references/shared.md)')
            link = ['demo/SKILL.md -> ../../references/shared.md']
            self.assertEqual(broken_links(plugin, skills), [])
            self.assertEqual(broken_links(skills), link)
            shared.unlink()
            self.assertEqual(broken_links(plugin, skills), link)

    def test_folder_link_needs_the_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'skill'
            (root / 'examples').mkdir(parents=True)
            (root / 'notes.md').write_text('Notes')
            (root / 'SKILL.md').write_text(
                '[examples](examples/) [gone](gone/) [file as folder](notes.md/) '
                '[folder as file](examples)')
            self.assertEqual(broken_links(root), [
                'SKILL.md -> gone/', 'SKILL.md -> notes.md/', 'SKILL.md -> examples'])

    def test_only_imported_text_may_link_a_skipped_upstream_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / 'plugin'
            skills = plugin / 'skills'
            for name in ('help', 'kept', 'authored'):
                (skills / name).mkdir(parents=True)
            (skills / 'kept/SKILL.md').write_text('Kept')
            (skills / 'help/SKILL.md').write_text(
                '[left out](../left-out/SKILL.md) [typo](../kpet/SKILL.md) '
                '[kept](../kept/SKILL.md) [outside](../../../left-out/SKILL.md) '
                '[never shipped](../left-out/never-shipped.md)')
            (skills / 'authored/SKILL.md').write_text('[left out](../left-out/SKILL.md)')
            source = 'vendor/pack'
            (plugin / 'upstream.lock.json').write_text(json.dumps({
                'upstream_root': source, 'files': [
                    {'upstream': f'{source}/skills/left-out/SKILL.md', 'status': 'skipped'},
                    {'upstream': f'{source}/skills/help/SKILL.md',
                     'path': 'skills/help/SKILL.md', 'status': 'injected'},
                    {'upstream': f'{source}/skills/kept/SKILL.md',
                     'path': 'skills/kept/SKILL.md', 'status': 'verbatim'},
                    {'path': 'skills/authored/SKILL.md', 'status': 'local'},
                    {'upstream': 'automations/other/SKILL.md', 'status': 'skipped'},
                    {'upstream': f'{source}/../skills/kpet/SKILL.md', 'status': 'skipped'}]}))
            self.assertEqual(upstream_lock.skipped_files(plugin), {'skills/left-out/SKILL.md'})
            self.assertEqual(upstream_lock.imported_skills(plugin), {'help', 'kept'})

            authored = 'authored/SKILL.md -> ../left-out/SKILL.md'
            left_out = 'help/SKILL.md -> ../left-out/SKILL.md'
            others = ['help/SKILL.md -> ../kpet/SKILL.md',
                      'help/SKILL.md -> ../../../left-out/SKILL.md',
                      'help/SKILL.md -> ../left-out/never-shipped.md']
            self.assertEqual(broken_links(plugin, skills), [authored, left_out, *others])
            gaps = (upstream_lock.imported_files(plugin), upstream_lock.skipped_files(plugin))
            self.assertEqual(broken_links(plugin, skills, gaps), [authored, *others])


if __name__ == '__main__':
    unittest.main()
