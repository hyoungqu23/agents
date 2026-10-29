"""Review references must survive copying just the skill directories."""
from pathlib import Path
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
