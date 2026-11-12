"""The independently shipped SPEC readers must implement the same contract."""
import importlib.util
from pathlib import Path
import unittest

from test_spec_handoff import sample


ROOT = Path(__file__).resolve().parents[2]
READERS = [ROOT / 'plugins' / plugin / 'skills' / skill / 'scripts/spec_handoff.py'
           for plugin, skill in (('product', 'spec'), ('build', 'implement'))]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def outcome(operation, value):
    try:
        return {'value': operation(value)}
    except ValueError as error:
        return {'error': str(error)}


class SpecHandoffParityTests(unittest.TestCase):
    def test_bundled_readers_are_identical(self):
        self.assertEqual(READERS[0].read_bytes(), READERS[1].read_bytes(),
                         'Update the canonical product SPEC reader and its standalone build copy together')

    def test_readers_agree_on_valid_and_rejected_sources(self):
        readers = [load(path, 'parity_reader_' + str(i)) for i, path in enumerate(READERS)]
        spec, questions = sample()
        corpus = [
            ('read_spec', spec, True),
            ('read_spec', spec.encode(), True),
            ('read_spec', spec.replace('| AC-empty |', '| AC-list |'), False),
            ('read_spec', spec.replace('| AC-empty |', 'AC-empty |'), False),
            ('read_spec', spec.replace('handoff_version: 1', 'handoff_version: 2'), False),
            ('read_spec', spec.replace('### 6.1', '```md\n### 6.1').replace('### 6.2', '```\n### 6.2'), False),
            ('read_spec', spec.encode() + b'\xff', False),
            ('read_questions', questions, True),
            ('read_questions', questions.replace('## 2.', '| Q-1 | decision | policy | AC-list | yes | deferred |\n## 2.'), True),
            ('read_questions', questions.replace('## 2.', '| Q-1 | decision | policy | AC-list | maybe | open |\n## 2.'), False),
            ('read_questions', questions.replace('## 2.', 'Q-1 | decision | policy | AC-list | yes | open |\n## 2.'), False),
        ]
        for operation, raw, accepted in corpus:
            with self.subTest(operation=operation, raw=raw):
                actual = [outcome(getattr(reader, operation), raw) for reader in readers]
                self.assertEqual(actual[0], actual[1])
                self.assertEqual('value' in actual[0], accepted)
        for reader in readers:
            self.assertEqual([r['AC ID'] for r in reader.read_spec(spec)['acs']], ['AC-list', 'AC-empty'])
            for impact, accepted in (('AC-list', True), ('AC-list, AC-empty', True), ('*', True),
                                     ('AC-unknown', False), ('AC-list~AC-empty', False)):
                with self.subTest(impact=impact):
                    value = outcome(lambda q: reader.affected_ids(q, ['AC-list', 'AC-empty']),
                                    {'영향 절·AC·범위': impact})
                    self.assertEqual('value' in value, accepted)


if __name__ == '__main__':
    unittest.main()
