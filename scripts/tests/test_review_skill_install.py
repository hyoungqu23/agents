"""Review references must survive copying just the skill directories."""
from pathlib import Path
import json
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / 'plugins/review/skills'


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
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / '.agents/skills'
            shutil.copytree(SKILLS, installed)
            self.assertEqual(broken_links(installed), [])

    def test_evaluation_inputs_stay_outside_distributed_skills(self):
        for plugin, skill in (('review', 'review-code'), ('product', 'prd-gate')):
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
