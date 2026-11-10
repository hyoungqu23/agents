"""Evaluator independently reads original ACs; no model/browser execution claims."""
import unittest
import test_implementation_behavioral as legacy
from test_source_coverage import spec_text


class OriginalCoverageEvaluationTests(unittest.TestCase):
    setUp = legacy.ImplementationEvaluationTests.setUp

    def test_missing_original_ac_is_detected_outside_manifest(self):
        source = self.output / 'SPEC.md'
        source.write_text(spec_text())
        inputs = {'requirements': [{'id': f'AC-{i}', 'source': 'spec', 'disposition': 'required'} for i in (1, 2)]}
        report = {'requirements': [{'id': f'AC-{i}', 'state': 'implemented'} for i in (1, 2)]}
        sources = {'spec': {'path': str(source)}}
        self.assertFalse(legacy.evaluation.requirement_coverage(inputs, report, sources, self.source))
        inputs['requirements'].append({'id': 'AC-3', 'source': 'spec', 'disposition': 'required'})
        report['requirements'].append({'id': 'AC-3', 'state': 'implemented'})
        self.assertTrue(legacy.evaluation.requirement_coverage(inputs, report, sources, self.source))

    def test_unsupported_original_does_not_pass_empty(self):
        source = self.output / 'SPEC.md'
        source.write_text(spec_text().replace('handoff_version: 1', 'handoff_version: 8'))
        with self.assertRaises(ValueError):
            legacy.evaluation.requirement_coverage({'requirements': []}, {'requirements': []},
                                                  {'spec': {'path': str(source)}}, self.source)

    def test_malformed_original_row_cannot_pass_a_truncated_execution_list(self):
        source = self.output / 'SPEC.md'
        source.write_text(spec_text().replace('| AC-3 |', 'AC-3 |'))
        with self.assertRaises(ValueError):
            legacy.evaluation.requirement_coverage({'requirements': []}, {'requirements': []},
                                                  {'spec': {'path': str(source)}}, self.source)
