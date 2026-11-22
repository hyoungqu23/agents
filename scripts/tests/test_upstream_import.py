"""Checks for plugins that import files from another repository.

`scripts/import_upstream.py` writes `upstream.lock.json`; these tests hold every
commit to it. What only a checkout of the upstream repository can show, such as
an upstream file the lock never mentions, is checked by `check --source`.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))
import import_upstream  # noqa: E402
import sync_upstream_pr  # noqa: E402
import upstream_lock  # noqa: E402

REPO_ROOT = Path(__file__).parents[2]
LOCKED_PLUGINS = sorted(
    path.parent for path in (REPO_ROOT / 'plugins').glob(f'*/{upstream_lock.LOCK_NAME}'))

# pstack names another skill as "the **arena** skill" and a principle skill as
# "the **prove-it-works** principle". test_skill_delegation.py reads neither.
NAMED = re.compile(r'\*\*([a-z][a-z0-9-]*)\*\* (skill|principle)\b')
ANCHOR = 'Read [the adapter](../../docs/adapter.md) first.'
LINE = 'Then read [the second adapter](../../docs/second.md).'


def unknown_skill_names(plugin):
    """Imported skill text that names a skill the plugin neither has nor skipped."""
    lock = upstream_lock.read(plugin)
    known = {path.parent.name for path in plugin.glob('skills/*/SKILL.md')}
    known |= {Path(path).parent.name for path in upstream_lock.skipped_files(plugin)
              if re.fullmatch(r'skills/[^/]+/SKILL\.md', path)}
    known |= set(lock.get('external_skills', []))
    failures = []
    for path in sorted(upstream_lock.imported_files(plugin)):
        if not path.startswith('skills/') or not path.endswith('.md'):
            continue
        text = (plugin / path).read_text(encoding='utf-8')
        for name, kind in NAMED.findall(text):
            skill = f'principle-{name}' if kind == 'principle' else name
            if skill not in known and name not in known:
                failures.append(f'{path}: {name} {kind}')
    return sorted(set(failures))


class LockedPluginTests(unittest.TestCase):
    def test_the_lock_matches_the_plugin_folder(self):
        self.assertTrue(LOCKED_PLUGINS)
        for plugin in LOCKED_PLUGINS:
            with self.subTest(plugin=plugin.name):
                self.assertEqual(import_upstream.check(plugin), [])

    def test_imported_text_names_only_skills_the_plugin_accounts_for(self):
        for plugin in LOCKED_PLUGINS:
            with self.subTest(plugin=plugin.name):
                self.assertEqual(unknown_skill_names(plugin), [])

    def test_upstream_agent_definitions_are_not_registered(self):
        # Claude Code registers every file in a plugin's agents/ folder.
        for plugin in LOCKED_PLUGINS:
            with self.subTest(plugin=plugin.name):
                self.assertFalse((plugin / 'agents').exists())


def git(repo, *args):
    subprocess.run(
        ['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@example.com',
         '-c', 'commit.gpgsign=false', *args],
        check=True, capture_output=True)


class ImportFixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.source = root / 'upstream'
        self.pack = self.source / 'vendor/pack'
        self.write(self.pack / 'skills/alpha/SKILL.md', f'# Alpha\n\n{ANCHOR}\n\nUse the **beta** skill.\n')
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta\n\nSee the **gone** skill.\n')
        self.write(self.pack / 'skills/beta/run.sh', '#!/bin/sh\n')
        (self.pack / 'skills/beta/run.sh').chmod(0o755)
        self.write(self.pack / 'skills/gone/SKILL.md', '# Gone\n')
        self.write(self.pack / 'agents/helper.md', 'helper\n')
        self.write(self.pack / 'README.md', 'upstream readme\n')
        self.write(self.source / 'elsewhere/SKILL.md', 'outside the pack\n')
        git(self.source, 'init', '-q')
        self.commit('first')

        self.plugin = root / 'plugins/demo'
        self.write(self.plugin / 'README.md', 'ours\n')
        self.write(self.plugin / upstream_lock.LOCK_NAME, json.dumps({
            'commit': '', 'upstream_root': 'vendor/pack', 'skip': ['skills/gone/'],
            'relocate': {'agents/': 'upstream-agents/', 'README.md': 'UPSTREAM-README.md'},
            'inject': {'after': ANCHOR, 'line': LINE},
            'files': [{'path': 'README.md', 'status': 'local'}]}))

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        git(self.source, 'add', '-A')
        git(self.source, 'commit', '-q', '-m', message)

    def entries(self):
        return {entry.get('path') or entry['upstream']: entry
                for entry in import_upstream.read_lock(self.plugin)['files']}

    def problems(self, source=True):
        return import_upstream.check(self.plugin, self.source if source else None)


class SyncTests(ImportFixture):
    def test_first_import_places_files_and_records_them(self):
        report = import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertEqual(len(report['new']), 6)
        entries = self.entries()
        self.assertEqual(
            {path: entry['status'] for path, entry in entries.items()},
            {'README.md': 'local', 'UPSTREAM-README.md': 'verbatim',
             'upstream-agents/helper.md': 'verbatim', 'skills/alpha/SKILL.md': 'injected',
             'skills/beta/SKILL.md': 'verbatim', 'skills/beta/run.sh': 'verbatim',
             'vendor/pack/skills/gone/SKILL.md': 'skipped'})
        self.assertEqual((self.plugin / 'README.md').read_text(), 'ours\n')
        self.assertFalse((self.plugin / 'skills/gone').exists())
        self.assertFalse((self.plugin / 'agents').exists())
        self.assertEqual(
            (self.plugin / 'skills/alpha/SKILL.md').read_text(),
            f'# Alpha\n\n{ANCHOR}\n\n{LINE}\n\nUse the **beta** skill.\n')
        self.assertTrue((self.plugin / 'skills/beta/run.sh').stat().st_mode & 0o100)
        self.assertTrue(entries['skills/beta/run.sh']['executable'])
        self.assertNotIn('executable', entries['skills/beta/SKILL.md'])
        self.assertFalse((self.plugin / 'skills/beta/SKILL.md').stat().st_mode & 0o100)
        alpha = entries['skills/alpha/SKILL.md']
        self.assertNotEqual(alpha['upstream_blob'], alpha['applied_blob'])
        self.assertEqual(self.problems(), [])
        self.assertEqual(upstream_lock.skipped_files(self.plugin), {'skills/gone/SKILL.md'})
        self.assertEqual(upstream_lock.imported_skills(self.plugin), {'alpha', 'beta'})

    def test_running_again_changes_nothing(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        report = import_upstream.sync(self.plugin, self.source)
        self.assertFalse(any(report.values()))
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_upstream_change_is_followed_and_the_line_inserted_again(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.write(self.pack / 'skills/alpha/SKILL.md', f'# Alpha 2\n\n{ANCHOR}\n')
        # Upstream moves its anchor from one skill to another.
        self.write(self.pack / 'skills/beta/SKILL.md', f'# Beta\n\n{ANCHOR}\n')
        self.write(self.pack / 'skills/gone/extra.md', 'still skipped\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['updated'], [
            'vendor/pack/skills/alpha/SKILL.md', 'vendor/pack/skills/beta/SKILL.md'])
        self.assertEqual(report['new'], ['vendor/pack/skills/gone/extra.md'])
        self.assertEqual(
            (self.plugin / 'skills/alpha/SKILL.md').read_text(),
            f'# Alpha 2\n\n{ANCHOR}\n\n{LINE}\n')
        self.assertEqual(self.entries()['skills/beta/SKILL.md']['status'], 'injected')
        self.assertEqual(self.problems(), [])

    def test_new_upstream_file_waits_for_a_person(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.write(self.pack / 'skills/fresh/SKILL.md', '# Fresh\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['unclassified'], ['vendor/pack/skills/fresh/SKILL.md'])
        self.assertFalse((self.plugin / 'skills/fresh').exists())
        self.assertEqual(self.problems(source=False), [])
        self.assertEqual(self.problems(), [
            'vendor/pack/skills/fresh/SKILL.md: upstream file is not classified in the lock'])

    def test_file_deleted_upstream_is_reported_and_kept(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        (self.pack / 'agents/helper.md').unlink()
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['removed'], ['vendor/pack/agents/helper.md'])
        self.assertTrue((self.plugin / 'upstream-agents/helper.md').is_file())
        self.assertEqual(self.problems(), [
            'vendor/pack/agents/helper.md: listed but absent upstream; delete it or mark it local'])

    def test_uncommitted_upstream_edits_are_not_imported(self):
        (self.pack / 'skills/beta/SKILL.md').write_text('not committed\n')
        (self.pack / 'skills/beta/run.sh').chmod(0o644)
        self.write(self.pack / 'skills/untracked/SKILL.md', 'not tracked\n')
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertEqual(
            (self.plugin / 'skills/beta/SKILL.md').read_text(), '# Beta\n\nSee the **gone** skill.\n')
        self.assertTrue(import_upstream.is_executable(self.plugin / 'skills/beta/run.sh'))
        self.assertFalse((self.plugin / 'skills/untracked').exists())
        self.assertEqual(self.problems(), [])

    def test_upstream_file_that_would_replace_a_local_file_stops_before_writing(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        self.write(self.pack / 'skills/alpha/SKILL.md', '# Alpha, changed\n')
        # README.md is relocated, so only a new upstream file can land on ours.
        self.write(self.plugin / 'CHANGELOG.md', 'our history\n')
        lock = import_upstream.read_lock(self.plugin)
        lock['files'].append({'path': 'CHANGELOG.md', 'status': 'local'})
        import_upstream.write_lock(self.plugin, lock)
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        self.write(self.pack / 'CHANGELOG.md', 'their history\n')
        self.commit('second')
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertIn('CHANGELOG.md: is a file written in this repository', str(stopped.exception))
        self.assertEqual((self.plugin / 'CHANGELOG.md').read_text(), 'our history\n')
        self.assertIn(LINE, (self.plugin / 'skills/alpha/SKILL.md').read_text())
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_colliding_or_escaping_destinations_stop_before_writing(self):
        lock = import_upstream.read_lock(self.plugin)
        lock['relocate']['agents/'] = 'skills/beta/'
        import_upstream.write_lock(self.plugin, lock)
        self.write(self.pack / 'agents/run.sh', 'collides\n')
        self.write(self.plugin / 'skills/alpha/SKILL.md', 'written here, never listed\n')
        self.commit('second')
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        message = str(stopped.exception)
        self.assertIn('skills/beta/run.sh: two upstream files are placed here', message)
        self.assertIn('skills/alpha/SKILL.md: exists but the lock does not list it', message)
        self.assertFalse((self.plugin / 'skills/beta').exists())

        lock['relocate']['agents/'] = '../outside/'
        import_upstream.write_lock(self.plugin, lock)
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertIn('../outside/helper.md: leaves the plugin folder', str(stopped.exception))
        self.assertFalse((self.plugin.parent / 'outside').exists())

    def test_upstream_file_turned_folder_stops_before_writing(self):
        self.write(self.pack / 'skills/beta/templates', 'one file\n')
        self.commit('second')
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        (self.pack / 'skills/beta/templates').unlink()
        self.write(self.pack / 'skills/beta/templates/default.md', 'now a folder\n')
        self.write(self.pack / 'skills/alpha/SKILL.md', '# Alpha, changed\n')
        self.commit('third')
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertIn('skills/beta/templates is a file here; remove it first',
                      str(stopped.exception))
        self.assertIn(LINE, (self.plugin / 'skills/alpha/SKILL.md').read_text())
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_lock_names_the_commit_the_files_were_read_from(self):
        first = import_upstream.checked_out_commit(self.source)
        listing = import_upstream.upstream_files

        def moving(source, commit, root):
            files = listing(source, commit, root)
            self.write(self.pack / 'skills/beta/SKILL.md', '# Beta, later\n')
            self.commit('lands while sync runs')
            return files

        import_upstream.upstream_files = moving
        self.addCleanup(setattr, import_upstream, 'upstream_files', listing)
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        import_upstream.upstream_files = listing
        self.assertEqual(import_upstream.read_lock(self.plugin)['commit'], first)
        self.assertIn('**gone**', (self.plugin / 'skills/beta/SKILL.md').read_text())
        git(self.source, 'checkout', '-q', first)
        self.assertEqual(self.problems(), [])

    def test_skipped_file_deleted_upstream_leaves_the_lock(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        (self.pack / 'skills/gone/SKILL.md').unlink()
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['removed'], [])
        self.assertNotIn('vendor/pack/skills/gone/SKILL.md', self.entries())
        self.assertEqual(self.problems(), [])

    def patch_beta(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        target = self.plugin / 'skills/beta/SKILL.md'
        target.write_text('# Beta\n\nSee the **gone** skill.\n\nOur added step.\n')
        import_upstream.mark_patched(self.plugin, 'skills/beta/SKILL.md')
        self.assertEqual(self.problems(), [])
        return target

    def test_upstream_change_is_merged_into_a_patched_file(self):
        target = self.patch_beta()
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta, renamed\n\nSee the **gone** skill.\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['patched'], ['skills/beta/SKILL.md'])
        self.assertEqual(report['conflicts'], [])
        self.assertEqual(
            target.read_text(), '# Beta, renamed\n\nSee the **gone** skill.\n\nOur added step.\n')
        self.assertEqual(self.entries()['skills/beta/SKILL.md']['status'], 'patched')
        self.assertEqual(self.problems(), [])

    def test_untouched_patched_file_is_left_alone(self):
        target = self.patch_beta()
        before = target.read_bytes()
        self.write(self.pack / 'README.md', 'changed elsewhere\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['patched'], ['skills/beta/SKILL.md'])
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(self.problems(), [])

    def test_new_upstream_file_cannot_take_the_place_of_a_kept_patched_file(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        target = self.plugin / 'upstream-agents/helper.md'
        target.write_text('helper, patched\n')
        import_upstream.mark_patched(self.plugin, 'upstream-agents/helper.md')
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        self.write(self.pack / 'upstream-agents/helper.md', 'another helper\n')
        self.commit('second')
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertIn('upstream-agents/helper.md: already holds the upstream file '
                      'vendor/pack/agents/helper.md', str(stopped.exception))
        self.assertEqual(target.read_text(), 'helper, patched\n')
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_unrecorded_edit_to_a_patched_file_is_not_merged_into_the_patch(self):
        target = self.patch_beta()
        target.write_text(target.read_text() + '\nA draft nobody recorded.\n')
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        # Upstream changing another file only must stop too, then the patched one.
        for changed in ('README.md', 'skills/beta/SKILL.md'):
            self.write(self.pack / changed, '# Beta, renamed\n\nSee the **gone** skill.\n')
            self.commit(f'change {changed}')
            with self.subTest(changed=changed), self.assertRaises(SystemExit) as stopped:
                import_upstream.sync(self.plugin, self.source)
            self.assertIn('skills/beta/SKILL.md: differs from the recorded patch',
                          str(stopped.exception))
            self.assertIn('A draft nobody recorded.', target.read_text())
            self.assertEqual((self.plugin / 'UPSTREAM-README.md').read_text(), 'upstream readme\n')
            self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_unrecorded_edit_to_a_patched_file_deleted_upstream_stops_too(self):
        target = self.patch_beta()
        target.write_text(target.read_text() + '\nA draft nobody recorded.\n')
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        (self.pack / 'skills/beta/SKILL.md').unlink()
        self.write(self.pack / 'README.md', 'changed too\n')
        self.commit('second')
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source)
        self.assertIn('skills/beta/SKILL.md: differs from the recorded patch', str(stopped.exception))
        self.assertEqual((self.plugin / 'UPSTREAM-README.md').read_text(), 'upstream readme\n')
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)

    def test_skip_written_from_the_repository_root_is_refused(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.write(self.pack / 'skills/fresh/SKILL.md', '# Fresh\n')
        self.commit('second')
        lock = import_upstream.read_lock(self.plugin)
        lock['skip'].append('vendor/pack/skills/fresh/')
        import_upstream.write_lock(self.plugin, lock)
        with self.assertRaises(SystemExit) as stopped:
            import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertIn('skip: vendor/pack/skills/fresh/ starts with upstream_root',
                      str(stopped.exception))
        self.assertFalse((self.plugin / 'skills/fresh').exists())
        self.assertEqual(self.problems(source=False), [
            'skip: vendor/pack/skills/fresh/ starts with upstream_root; '
            'write it relative to vendor/pack/'])

    def test_executable_bit_change_alone_reaches_a_patched_file(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        target = self.plugin / 'skills/beta/run.sh'
        target.write_text('#!/bin/sh\necho ours\n')
        import_upstream.mark_patched(self.plugin, 'skills/beta/run.sh')
        (self.pack / 'skills/beta/run.sh').chmod(0o644)
        self.commit('second')
        import_upstream.sync(self.plugin, self.source)
        self.assertEqual(target.read_text(), '#!/bin/sh\necho ours\n')
        self.assertFalse(import_upstream.is_executable(target))
        self.assertNotIn('executable', self.entries()['skills/beta/run.sh'])
        self.assertEqual(self.problems(), [])

    def test_conflicting_upstream_change_leaves_markers_that_fail_the_check(self):
        target = self.patch_beta()
        self.write(self.pack / 'skills/beta/SKILL.md',
                   '# Beta\n\nSee the **gone** skill.\n\nTheir added step.\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['conflicts'], ['skills/beta/SKILL.md'])
        self.assertIn('<<<<<<< this repository', target.read_text())
        self.assertEqual(self.problems(), ['skills/beta/SKILL.md: has a merge conflict marker'])
        target.write_text('# Beta\n\nSee the **gone** skill.\n\nBoth steps.\n')
        self.assertEqual(self.problems(), [
            'skills/beta/SKILL.md: content does not match applied_blob'])
        import_upstream.mark_patched(self.plugin, 'skills/beta/SKILL.md')
        self.assertEqual(self.problems(), [])

    def test_patch_on_an_injected_file_keeps_the_generated_line(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        target = self.plugin / 'skills/alpha/SKILL.md'
        target.write_text(target.read_text().replace('**beta** skill', '**beta** skill here'))
        import_upstream.mark_patched(self.plugin, 'skills/alpha/SKILL.md')
        self.write(self.pack / 'skills/alpha/SKILL.md',
                   f'# Alpha 2\n\n{ANCHOR}\n\nUse the **beta** skill.\n')
        self.commit('second')
        report = import_upstream.sync(self.plugin, self.source)
        self.assertEqual(report['conflicts'], [])
        self.assertEqual(
            target.read_text(),
            f'# Alpha 2\n\n{ANCHOR}\n\n{LINE}\n\nUse the **beta** skill here.\n')

    def test_only_an_imported_file_can_be_marked_patched(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        for path in ('README.md', 'skills/gone/SKILL.md', 'nowhere.md'):
            with self.subTest(path=path), self.assertRaises(SystemExit):
                import_upstream.mark_patched(self.plugin, path)

    def test_upstream_version_is_copied_into_the_lock(self):
        self.write(self.pack / 'plugin.json', '{"version": "1.2.3"}')
        self.commit('second')
        lock = import_upstream.read_lock(self.plugin)
        lock.update(version_file='plugin.json', skip=[*lock['skip'], 'plugin.json'])
        import_upstream.write_lock(self.plugin, lock)
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertEqual(import_upstream.read_lock(self.plugin)['version'], '1.2.3')
        self.assertFalse((self.plugin / 'plugin.json').exists())

    def test_unreadable_upstream_version_stops_before_writing(self):
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        lock = import_upstream.read_lock(self.plugin)
        lock['version_file'] = 'plugin.json'
        import_upstream.write_lock(self.plugin, lock)
        before = (self.plugin / upstream_lock.LOCK_NAME).read_text()
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta 2\n')
        self.commit('second')
        with self.assertRaises(SystemExit):
            import_upstream.sync(self.plugin, self.source)
        self.assertEqual((self.plugin / 'skills/beta/SKILL.md').read_text(),
                         '# Beta\n\nSee the **gone** skill.\n')
        self.assertEqual((self.plugin / upstream_lock.LOCK_NAME).read_text(), before)


class CheckTests(ImportFixture):
    def setUp(self):
        super().setUp()
        import_upstream.sync(self.plugin, self.source, accept_new=True)

    def test_edited_imported_file_fails(self):
        self.write(self.plugin / 'skills/beta/SKILL.md', '# Beta, edited\n')
        self.assertEqual(self.problems(source=False), [
            'skills/beta/SKILL.md: content does not match upstream_blob'])

    def test_edited_injected_file_fails(self):
        target = self.plugin / 'skills/alpha/SKILL.md'
        target.write_text(target.read_text() + 'more\n')
        self.assertEqual(self.problems(source=False), [
            'skills/alpha/SKILL.md: content does not match applied_blob',
            'skills/alpha/SKILL.md: differs from upstream by more than the generated line'])

    def relock(self, path, **changes):
        lock = import_upstream.read_lock(self.plugin)
        for entry in lock['files']:
            if entry.get('path') == path:
                entry.update(changes)
        import_upstream.write_lock(self.plugin, lock)

    def test_injected_file_must_be_upstream_plus_the_generated_line(self):
        target = self.plugin / 'skills/alpha/SKILL.md'
        original = target.read_text()
        for text, problem in (
                (original.replace(f'\n{LINE}\n', ''),
                 'the generated line does not follow the anchor line'),
                (original.replace(LINE, 'Then read something else.'),
                 'the generated line does not follow the anchor line'),
                (original + 'An added step.\n',
                 'differs from upstream by more than the generated line')):
            with self.subTest(problem=problem, text=text):
                target.write_text(text)
                # Whoever edits the file can also update its hash.
                self.relock('skills/alpha/SKILL.md',
                            applied_blob=import_upstream.blob_id(target.read_bytes()))
                self.assertEqual(self.problems(source=False), [f'skills/alpha/SKILL.md: {problem}'])

    def test_changed_inject_rule_needs_a_new_sync(self):
        lock = import_upstream.read_lock(self.plugin)
        lock['inject']['line'] = 'Then read the renamed adapter.'
        import_upstream.write_lock(self.plugin, lock)
        self.assertEqual(self.problems(source=False), [
            'skills/alpha/SKILL.md: the generated line does not follow the anchor line'])
        import_upstream.sync(self.plugin, self.source)
        self.assertEqual(self.problems(), [])

    def test_file_with_the_anchor_cannot_be_listed_verbatim(self):
        target = self.plugin / 'skills/alpha/SKILL.md'
        target.write_text(target.read_text().replace(f'\n{LINE}\n', ''))
        lock = import_upstream.read_lock(self.plugin)
        for entry in lock['files']:
            if entry.get('path') == 'skills/alpha/SKILL.md':
                entry['status'] = 'verbatim'
                del entry['applied_blob']
        import_upstream.write_lock(self.plugin, lock)
        self.assertEqual(self.problems(source=False), [
            'skills/alpha/SKILL.md: has the anchor line, so sync would insert the generated line'])

    def test_lost_executable_bit_fails(self):
        (self.plugin / 'skills/beta/run.sh').chmod(0o644)
        self.assertEqual(self.problems(source=False), [
            'skills/beta/run.sh: executable bit does not match the lock'])
        # Editing the lock to agree is caught against the checkout.
        lock = import_upstream.read_lock(self.plugin)
        for entry in lock['files']:
            entry.pop('executable', None)
        import_upstream.write_lock(self.plugin, lock)
        self.assertEqual(self.problems(source=False), [])
        self.assertEqual(self.problems(), [
            'vendor/pack/skills/beta/run.sh: executable bit does not match upstream'])

    def test_conflict_marker_fails_even_when_the_hash_was_updated(self):
        target = self.plugin / 'skills/beta/SKILL.md'
        target.write_text('<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\n')
        lock = import_upstream.read_lock(self.plugin)
        for entry in lock['files']:
            if entry.get('path') == 'skills/beta/SKILL.md':
                entry.update(status='patched',
                             applied_blob=import_upstream.blob_id(target.read_bytes()))
        import_upstream.write_lock(self.plugin, lock)
        self.assertEqual(self.problems(source=False), [
            'skills/beta/SKILL.md: has a merge conflict marker'])

    def test_missing_and_unlisted_files_fail(self):
        (self.plugin / 'upstream-agents/helper.md').unlink()
        self.write(self.plugin / 'skills/authored/SKILL.md', 'written here\n')
        self.assertEqual(self.problems(source=False), [
            'upstream-agents/helper.md: listed as verbatim but is not a regular file',
            f'skills/authored/SKILL.md: not listed in {upstream_lock.LOCK_NAME}'])

    def test_lock_that_misstates_upstream_fails_against_the_checkout(self):
        # A file written here and listed as verbatim passes the folder check,
        # because its hash is its own. Only the checkout shows upstream lacks it.
        self.write(self.plugin / 'skills/authored/SKILL.md', 'written here\n')
        lock = import_upstream.read_lock(self.plugin)
        lock['files'].append({
            'upstream': 'vendor/pack/skills/authored/SKILL.md',
            'path': 'skills/authored/SKILL.md', 'status': 'verbatim',
            'upstream_blob': import_upstream.blob_id(b'written here\n')})
        for entry in lock['files']:
            if entry.get('path') == 'skills/beta/run.sh':
                entry['upstream_blob'] = import_upstream.blob_id(b'#!/bin/sh\nrm -rf x\n')
        import_upstream.write_lock(self.plugin, lock)
        (self.plugin / 'skills/beta/run.sh').write_text('#!/bin/sh\nrm -rf x\n')
        self.assertEqual(self.problems(source=False), [])
        self.assertEqual(self.problems(), [
            'vendor/pack/skills/authored/SKILL.md: listed but absent upstream; '
            'delete it or mark it local',
            'vendor/pack/skills/beta/run.sh: upstream_blob does not match upstream'])

    def test_checkout_at_another_commit_is_refused(self):
        self.write(self.pack / 'README.md', 'changed\n')
        self.commit('second')
        self.assertEqual(len(self.problems()), 1)
        self.assertIn("not at the lock's commit", self.problems()[0])

    def test_check_can_fetch_the_lock_commit_itself(self):
        lock = import_upstream.read_lock(self.plugin)
        lock['repository'] = self.source.as_uri()
        import_upstream.write_lock(self.plugin, lock)
        fetched = self.plugin.parent / 'fetched'
        self.assertEqual(import_upstream.main(
            ['check', '--plugin', str(self.plugin), '--fetch', str(fetched / '1')]), 0)
        # An existing checkout is refused: fetching into it would detach its HEAD.
        branch = import_upstream.git_output(self.source, 'symbolic-ref', 'HEAD')
        for used in (fetched / '1', self.source):
            with self.subTest(directory=used), self.assertRaises(SystemExit):
                import_upstream.main(['check', '--plugin', str(self.plugin), '--fetch', str(used)])
        self.assertEqual(import_upstream.git_output(self.source, 'symbolic-ref', 'HEAD'), branch)
        self.write(self.pack / 'skills/fresh/SKILL.md', '# Fresh\n')
        self.commit('second')
        # The fetch pins the lock's commit, so later upstream commits do not matter.
        self.assertEqual(import_upstream.main(
            ['check', '--plugin', str(self.plugin), '--fetch', str(fetched / '2')]), 0)
        (self.plugin / 'skills/beta/run.sh').chmod(0o644)
        self.assertEqual(import_upstream.main(
            ['check', '--plugin', str(self.plugin), '--fetch', str(fetched / '3')]), 1)

    def test_path_leaving_the_plugin_fails(self):
        lock = import_upstream.read_lock(self.plugin)
        lock['files'].append({'path': '../../README.md', 'status': 'local'})
        import_upstream.write_lock(self.plugin, lock)
        self.assertIn('../../README.md: leaves the plugin folder', self.problems(source=False))

    def test_names_of_skills_the_plugin_lacks_are_found(self):
        self.assertEqual(unknown_skill_names(self.plugin), [])
        target = self.pack / 'skills/beta/SKILL.md'
        target.write_text(
            'Use the **alpha** skill, the **gone** skill, the **builtin** skill, '
            'the **missing** skill and the **absent** principle.\n')
        self.write(self.pack / 'skills/principle-kept/SKILL.md', 'The **kept** principle.\n')
        self.commit('second')
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.assertEqual(unknown_skill_names(self.plugin), [
            'skills/beta/SKILL.md: absent principle', 'skills/beta/SKILL.md: builtin skill',
            'skills/beta/SKILL.md: missing skill'])
        lock = import_upstream.read_lock(self.plugin)
        lock['external_skills'] = ['builtin']
        import_upstream.write_lock(self.plugin, lock)
        self.assertEqual(unknown_skill_names(self.plugin), [
            'skills/beta/SKILL.md: absent principle', 'skills/beta/SKILL.md: missing skill'])


class SyncPullRequestTests(ImportFixture):
    def setUp(self):
        super().setUp()
        self.repo = self.plugin.parents[1]
        lock = import_upstream.read_lock(self.plugin)
        lock['repository'] = 'https://github.com/example/pack'
        lock['files'] += [{'path': path, 'status': 'local'}
                          for path in ('.claude-plugin/plugin.json', 'CHANGELOG.md')]
        import_upstream.write_lock(self.plugin, lock)
        self.write(self.plugin / '.claude-plugin/plugin.json',
                   '{\n  "name": "demo",\n  "version": "0.1.9"\n}\n')
        self.write(self.plugin / 'CHANGELOG.md', '# Changelog\n\n## 0.1.9 - 2026-01-01\n\n- First.\n')
        self.write(self.repo / '.claude-plugin/marketplace.json', json.dumps(
            {'plugins': [{'name': 'other', 'version': '3.0.0'},
                         {'name': 'demo', 'version': '0.1.9'}]}, indent=4) + '\n')
        import_upstream.sync(self.plugin, self.source, accept_new=True)
        self.first = import_upstream.read_lock(self.plugin)['commit']

    def prepare(self):
        return sync_upstream_pr.prepare(self.repo, self.plugin, self.source, '2026-02-03')

    def test_change_outside_the_imported_folder_prepares_nothing(self):
        self.write(self.source / 'elsewhere/SKILL.md', 'changed outside the pack\n')
        self.commit('second')
        before = {path: path.read_bytes() for path in self.repo.rglob('*') if path.is_file()}
        self.assertIsNone(self.prepare())
        self.assertEqual(
            {path: path.read_bytes() for path in self.repo.rglob('*') if path.is_file()}, before)
        self.assertEqual(import_upstream.read_lock(self.plugin)['commit'], self.first)

    def test_upstream_change_is_released_as_the_next_patch_version(self):
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta 2\n')
        self.write(self.pack / 'skills/fresh/SKILL.md', '# Fresh\n')
        (self.pack / 'agents/helper.md').unlink()
        self.commit('second')
        second = import_upstream.checked_out_commit(self.source)
        text = self.prepare()

        manifest = (self.plugin / '.claude-plugin/plugin.json').read_text()
        self.assertEqual(manifest, '{\n  "name": "demo",\n  "version": "0.1.10"\n}\n')
        marketplace = json.loads((self.repo / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual([entry['version'] for entry in marketplace['plugins']], ['3.0.0', '0.1.10'])
        self.assertIn('\n    "plugins"', (self.repo / '.claude-plugin/marketplace.json').read_text())
        notes = (self.plugin / 'CHANGELOG.md').read_text()
        self.assertTrue(notes.startswith(
            f'# Changelog\n\n## 0.1.10 - 2026-02-03\n\n- Sync with `example/pack` at `{second[:7]}`'))
        self.assertIn('## 0.1.9 - 2026-01-01', notes)
        sys.path.insert(0, str(REPO_ROOT / 'scripts'))
        import check_release_notes
        self.assertIsNone(check_release_notes.check_notes('0.1.10', notes))

        self.assertIn(f'https://github.com/example/pack/compare/{self.first}...{second}', text)
        self.assertIn(
            '### 분류되지 않은 새 원문 파일 (`vendor/pack` 기준 경로)\n\n- `skills/fresh/SKILL.md`', text)
        self.assertIn('### 원문에서 지워진 파일\n\n- `vendor/pack/agents/helper.md`', text)
        self.assertIn('### 충돌이 남은 파일\n\n- 없음', text)
        self.assertIn('### 내용이 바뀐 원문 파일\n\n- `vendor/pack/skills/beta/SKILL.md`', text)
        self.assertEqual(import_upstream.check(self.plugin), [])

    def test_unreleased_entries_move_into_the_new_release(self):
        self.write(self.plugin / 'CHANGELOG.md',
                   '# Changelog\n\n## Unreleased\n\n- Pending.\n\n## 0.1.9 - 2026-01-01\n\n- First.\n')
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta 2\n')
        self.commit('second')
        self.prepare()
        notes = (self.plugin / 'CHANGELOG.md').read_text()
        self.assertRegex(notes, r'^# Changelog\n\n## Unreleased\n\n## 0\.1\.10 - 2026-02-03\n\n'
                                r'- Sync with [^\n]+\n- Pending\.\n\n## 0\.1\.9 - 2026-01-01\n')
        sys.path.insert(0, str(REPO_ROOT / 'scripts'))
        import check_release_notes
        self.assertIsNone(check_release_notes.check_notes('0.1.10', notes))

    def test_unreleased_entries_below_a_release_move_too(self):
        self.write(self.plugin / 'CHANGELOG.md',
                   '# Changelog\n\n## 0.1.9 - 2026-01-01\n\n- First.\n\n##  Unreleased\t\n\n- Pending.\n')
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta 2\n')
        self.commit('second')
        self.prepare()
        notes = (self.plugin / 'CHANGELOG.md').read_text()
        self.assertRegex(notes, r'^# Changelog\n\n## 0\.1\.10 - 2026-02-03\n\n- Sync with [^\n]+\n'
                                r'- Pending\.\n\n## 0\.1\.9 - 2026-01-01\n\n- First\.\n\n##  Unreleased\t\n\n$')
        sys.path.insert(0, str(REPO_ROOT / 'scripts'))
        import check_release_notes
        self.assertIsNone(check_release_notes.check_notes('0.1.10', notes))

    def test_a_release_that_cannot_finish_writes_nothing(self):
        self.write(self.pack / 'skills/beta/SKILL.md', '# Beta 2\n')
        self.commit('second')
        broken = {'.claude-plugin/marketplace.json': b'{"plugins": []}',
                  'plugins/demo/CHANGELOG.md': b'# Changelog \xff\n',
                  'plugins/demo/.claude-plugin/plugin.json': b'{"name": "demo", "version": "1.0"}'}
        for name, content in broken.items():
            with self.subTest(file=name):
                path = self.repo / name
                good = path.read_bytes()
                path.write_bytes(content)
                before = {found: found.read_bytes()
                          for found in self.repo.rglob('*') if found.is_file()}
                with self.assertRaises(SystemExit):
                    self.prepare()
                self.assertEqual({found: found.read_bytes()
                                  for found in self.repo.rglob('*') if found.is_file()}, before)
                path.write_bytes(good)
        self.assertIsNotNone(self.prepare())


if __name__ == '__main__':
    unittest.main()
