import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
grader = runpy.run_path(str(ROOT / 'reports/review-pr-resume-2026-10-15/forward_test.py'))


class SubmissionGraderTests(unittest.TestCase):
    def test_extra_submission_attempt_fails_even_if_recorded_as_get(self):
        check = grader['pending_only_cli_calls']
        pending = ['api', '--method', 'POST', 'graphql', '--input', '-']
        legitimate = [pending]
        records = [{'method': 'POST', 'endpoint': 'graphql'}]
        self.assertTrue(check(legitimate, records))
        endpoint = 'repos/example/project/pulls/7/reviews/91/events'
        for extra in (
            ['api', '-X', 'POST', endpoint, '-f', 'event=COMMENT'],
            ['api', endpoint],
            ['api', 'graphql', '-f', 'query=mutation{submitPullRequestReview}'],
            ['pr', 'review', '--comment'],
            *(['api', 'graphql', flag] for flag in
              ('-XPOST', '-fquery=foo', '-Fquery=foo', '--field=query=foo',
               '--raw-field=query=foo', '--method=POST')),
        ):
            with self.subTest(extra=extra):
                self.assertFalse(check([*legitimate, extra], [*records, {'method': 'GET'}]))
                self.assertFalse(check([*legitimate, extra], records))
