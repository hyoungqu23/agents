"""Exercise capability refusal and input preservation with process doubles."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('reviewer_bridge', ROOT / 'scripts/behavioral/reviewer.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class ReviewerBridgeTests(unittest.TestCase):
    def run_bridge(self, body, request=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);workspace=root/'workspace';workspace.mkdir();evidence=root/'evidence';evidence.mkdir()
            for name in ('problem.md','prd.md','chain-notes.md'):
                (workspace/name).write_text(name+' original content')
            authored={name:hashlib.sha256((workspace/name).read_bytes()).hexdigest() for name in ('problem.md','prd.md')}
            (workspace/'authored.sha256.json').write_text(json.dumps(authored))
            (workspace/'review-prompt.txt').write_text('Review only')
            (workspace/'review-request.json').write_text(json.dumps(request if request is not None else
                {'action':'review','prompt_path':'review-prompt.txt'}))
            bridge=module.ReviewerBridge([sys.executable,'-c',body],workspace,evidence,time.monotonic()+5,'process-double')
            bridge.start();bridge.thread.join(timeout=7);bridge.stop()
            result=json.loads((evidence/'reviewer-result.json').read_text())
            return result,{p.name:p.read_text() for p in workspace.iterdir() if p.is_file()},(evidence/'reviewer-launch.json').exists()

    def test_only_fixed_request_can_launch_a_reviewer(self):
        result,files,launched=self.run_bridge("from pathlib import Path;Path('invoked').write_text('yes')",
            {'action':'shell','command':'unapproved'})
        self.assertEqual(result['status'],'failed');self.assertFalse(launched);self.assertNotIn('invoked',files)

    def test_completed_reviewer_preserves_inputs_and_records_host_launch(self):
        result,files,launched=self.run_bridge("import sys;from pathlib import Path;sys.stdin.read();Path('report.md').write_text('review');print('{\"type\":\"turn.completed\"}')")
        self.assertTrue(launched);self.assertEqual(result['status'],'completed')
        self.assertEqual(result['before_sha256'],result['after_sha256']);self.assertEqual(files['report.md'],'review')

    def test_zero_exit_without_completed_turn_is_failure(self):
        for body in ("print('{}')", "print('[]')"):
            with self.subTest(body=body):
                result,_,launched=self.run_bridge(body)
                self.assertTrue(launched);self.assertEqual(result['status'],'failed')

    def test_input_mutation_is_failure_despite_completed_turn(self):
        result,_,_=self.run_bridge("from pathlib import Path;Path('prd.md').write_text('changed');print('{\"type\":\"turn.completed\"}')")
        self.assertEqual(result['status'],'failed');self.assertNotEqual(result['before_sha256'],result['after_sha256'])


if __name__ == '__main__':
    unittest.main()
