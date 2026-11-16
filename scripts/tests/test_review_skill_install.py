"""Skill references must survive copying just a plugin's skill directories."""
from pathlib import Path
import json
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOTS = sorted((ROOT / 'plugins').glob('*/skills'))
# Template links that resolve only after the template is saved as the real
# SPEC.md and QUESTIONS.md, which sit beside each other in the target project.
TEMPLATE_LINKS = {
    'spec/assets/SPEC.template.md -> ./QUESTIONS.md',
    'spec/assets/QUESTIONS.template.md -> ./SPEC.md',
}


def broken_links(root):
    failures = []
    for source in sorted(root.rglob('*.md')):
        if 'evals' in source.relative_to(root).parts:
            continue
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', source.read_text()):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (source.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                failures.append(f'{source.relative_to(root)} -> {link}')
    return failures


class ReviewSkillInstallTests(unittest.TestCase):
    def test_references_survive_skill_directory_install(self):
        skills = [path for root in SKILL_ROOTS for path in root.glob('*/SKILL.md')]
        self.assertEqual(len(skills), 18)
        excluded = set()
        for skill_root in SKILL_ROOTS:
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
                broken = set(broken_links(installed / 'skills'))
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


if __name__ == '__main__':
    unittest.main()
