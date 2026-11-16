"""Exercise CI comparisons on diverging branches, independent of repository history."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'check_release_notes.py'


class ReleaseNotesTests(unittest.TestCase):
    def test_event_ranges_and_release_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            plugin = repo / 'plugins' / 'sample'
            manifest = plugin / '.claude-plugin' / 'plugin.json'
            manifest.parent.mkdir(parents=True)
            notes = plugin / 'CHANGELOG.md'

            def git(*args):
                return subprocess.check_output(['git', '-C', directory, *args], text=True).strip()

            def commit(version, headings):
                manifest.write_text(json.dumps({'version': version}))
                notes.write_text(headings)
                git('add', '.')
                git('-c', 'user.email=test@example.org', '-c', 'user.name=Test',
                    'commit', '-qm', 'release fixture')
                return git('rev-parse', 'HEAD')

            def check(event, base, head, error=None):
                result = subprocess.run([sys.executable, SCRIPT, event, base, head],
                                        cwd=directory, capture_output=True, text=True)
                if error:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(error, result.stderr)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)

            git('init', '-q')
            start = commit('1.0.0', '## 1.0.0\n')
            unchanged = commit('1.0.0', '## Unreleased\n- queued\n## 1.0.0\n')
            check('push', start, unchanged)
            fixed = commit('1.1.0', '## Unreleased\n\n## 1.1.0\n- shipped\n')
            check('push', unchanged, fixed)
            git('checkout', '-q', '--detach', start)
            for content in ('## 1.1.0\n## Unreleased\n- queued\n',
                            '## Unreleased\n- queued\n## 1.1.0\n',
                            '## [Unreleased]\n- queued\n## [1.1.0]\n'):
                bad = commit('1.1.0', content)
                check('pull_request', fixed, bad, 'Unreleased')
            mismatch = commit('1.2.0', '## 1.1.0\n')
            check('push', bad, mismatch, '1.2.0')
            check('push', 'missing-base', fixed, 'fatal')
            codex_manifest = plugin / '.codex-plugin' / 'plugin.json'
            codex_manifest.parent.mkdir()
            codex_manifest.write_text(json.dumps({'version': '2.0.0'}))
            codex_change = commit('1.2.0', '## 1.2.0\n')
            check('push', mismatch, codex_change, '2.0.0')
