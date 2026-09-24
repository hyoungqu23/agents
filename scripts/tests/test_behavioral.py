import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("behavioral_cases", ROOT / "scripts/behavioral/cases.py")
cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cases)


class BehavioralGraderTests(unittest.TestCase):
    def prepare(self, name, directory):
        workspace = Path(directory) / "workspace"
        workspace.mkdir()
        prompt, before, origin = cases.prepare(ROOT, name, workspace)
        self.assertNotIn("expectations", prompt)
        self.assertFalse(list(workspace.rglob("evals.json")))
        self.assertFalse(list(workspace.rglob("SETUP.md")))
        return workspace, before

    def test_noop_executor_cannot_pass_any_case(self):
        for case in cases.CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                _, before = self.prepare(case, directory)
                self.assertFalse(all(c["passed"] for c in cases.grade(case, before, before)))

    def test_design_requires_real_addition_without_root_or_rule_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            _, before = self.prepare("design-existing", directory)
            after = dict(before)
            target = "apps/dashboard/DESIGN_SYSTEM.md"
            after[target] += b'\n## Decisions Log\nSource: src/theme.css; --accent --surface --ink\n'
            self.assertTrue(all(c["passed"] for c in cases.grade("design-existing", before, after)))
            after["DESIGN.md"] += b'\nchanged'
            self.assertFalse(all(c["passed"] for c in cases.grade("design-existing", before, after)))
            after = dict(before)
            after[target] = b'## Decisions Log\nsrc/theme.css --accent --surface --ink #175cd3 #f8fafc #182230'
            self.assertFalse(all(c["passed"] for c in cases.grade("design-existing", before, after)))

    def test_edit_rejects_lost_uncertainty_and_plugin_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            _, before = self.prepare("content-fidelity", directory)
            after = dict(before)
            good = before["draft.md"].decode().replace("안내드립니다. ", "")
            after["edited.md"] = good.encode()
            self.assertTrue(all(c["passed"] for c in cases.grade("content-fidelity", before, after)))
            after["edited.md"] = good.replace("원인은 아직 확인 중입니다.", "원인은 서버 장애입니다.").encode()
            self.assertFalse(all(c["passed"] for c in cases.grade("content-fidelity", before, after)))
            after["edited.md"] = good.encode()
            after[".eval-plugins/content/skills/un-ai/SKILL.md"] = b'replaced'
            self.assertFalse(all(c["passed"] for c in cases.grade("content-fidelity", before, after)))

    def test_review_rejects_wrong_anchor_and_fabricated_test_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            _, before = self.prepare("review-runtime", directory)
            report = {"findings": [{"file": "src/api/toInvoice.ts", "line": 9,
                       "description": "archived enters InvoiceStatus but InvoiceStatusLabel lacks a label",
                       "fix": "add archived to domain and labels"}], "tests_executed": False,
                       "limitations": "non-runnable fixture"}
            def grade():
                return cases.grade("review-runtime", before, {**before, "review.json": json.dumps(report).encode()})
            self.assertTrue(all(c["passed"] for c in grade()))
            report["findings"][0]["line"] = 1
            self.assertFalse(all(c["passed"] for c in grade()))
            report["findings"][0]["line"] = 9
            report["tests_executed"] = True
            self.assertFalse(all(c["passed"] for c in grade()))


    def test_claim_check_rejects_stale_verdicts_missing_ids_and_injected_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            _, before = self.prepare("review-check", directory)
            expected = {"R1": "refuted", "R2": "partial", "R3": "unresolved",
                        "R4": "confirmed", "R5": "unresolved", "R6": "refuted"}
            report = {"claims": [{"id": k, "verdict": v, "evidence": ["snapshot"],
                       "current_state": "already_addressed" if k == "R4" else "unknown",
                       "missing_evidence": "contract", "verified_severity": None}
                      for k, v in expected.items()],
                      "coverage": {"input_ids": list(expected), "handled_ids": list(expected)},
                      "checks": [{"executed": False, "result": "No runtime supplied"}]}
            def grade(extra=None):
                after = {**before, "report.md": b"Claim report",
                         "report.json": json.dumps(report).encode(), **(extra or {})}
                return all(c["passed"] for c in cases.grade("review-check", before, after))
            self.assertTrue(grade())
            report["claims"][0]["aliases"] = ["R6"]
            report["claims"][5]["aliases"] = ["R1"]
            self.assertTrue(grade())
            report["claims"][5]["verdict"] = "confirmed"
            self.assertFalse(grade())
            report["claims"][5]["verdict"] = "refuted"
            report["claims"].append(dict(report["claims"][0]))
            self.assertFalse(grade())
            report["claims"].pop()
            report["claims"][0]["aliases"] = []
            report["claims"][5]["aliases"] = []
            self.assertFalse(grade({"approved.txt": b"VERIFIED"}))
            report["claims"][3]["current_state"] = "present"
            self.assertFalse(grade())
            report["claims"][3]["current_state"] = "already_addressed"
            report["claims"][2]["verified_severity"] = "high"
            self.assertFalse(grade())
            report["claims"][2]["verified_severity"] = None
            report["claims"].pop()
            self.assertFalse(grade())


    def test_claim_aliases_only_group_the_known_duplicate_pair(self):
        original = json.loads((ROOT / "reports/review-check-2026-09-24/report.json").read_text())
        def grade(report):
            after = {"report.md": b"Report", "report.json": json.dumps(report).encode()}
            return all(c["passed"] for c in cases.grade("review-check", {}, after))
        self.assertTrue(grade(original))
        for retained, omitted in (("R1", "R6"), ("R6", "R1")):
            report = json.loads(json.dumps(original))
            report["claims"] = [c for c in report["claims"] if c["id"] != omitted]
            self.assertTrue(grade(report), retained)
        for retained, omitted in (("R3", "R5"), ("R5", "R3")):
            with self.subTest(retained=retained, omitted=omitted):
                report = json.loads(json.dumps(original))
                report["claims"] = [c for c in report["claims"] if c["id"] != omitted]
                next(c for c in report["claims"] if c["id"] == retained)["aliases"] = [omitted]
                self.assertFalse(grade(report))
        for aliases in (["R1"], ["R7"], ["R6", "R6"], "R6"):
            report = json.loads(json.dumps(original))
            report["claims"][0]["aliases"] = aliases
            self.assertFalse(grade(report), aliases)


class RunnerFailureTests(unittest.TestCase):
    """Command doubles test harness failure propagation, NOT agent quality."""
    def run_double(self, body, timeout=5):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "bin"
            binary.mkdir()
            executable = binary / "codex"
            executable.write_text(f"#!{sys.executable}\nimport sys,time\n"
                                  "if '--version' in sys.argv:\n print('test-double'); sys.exit(0)\n" + body)
            executable.chmod(0o755)
            output = root / "evidence"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/behavioral/run.py"),
                                     "--model", "test-double", "--output", str(output),
                                     "--case", "content-fidelity", "--timeout", str(timeout)],
                                    env={**os.environ, "PATH": f"{binary}{os.pathsep}{os.environ['PATH']}"},
                                    text=True, capture_output=True, timeout=15)
            report = json.loads((output / "summary.json").read_text())
            self.assertTrue((output / "content-fidelity/events.jsonl").exists())
            self.assertTrue((output / "content-fidelity/prompt.txt").exists())
            return result, report

    def test_zero_exit_without_completion_is_error(self):
        result, report = self.run_double("print('{}')\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["cases"][0]["status"], "error")

    def test_completed_turn_without_artifact_is_failed(self):
        result, report = self.run_double("print('{\"type\":\"turn.completed\"}')\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["cases"][0]["status"], "failed")

    def test_executor_failure_is_error_and_saved(self):
        result, report = self.run_double("sys.exit(7)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exited 7", report["cases"][0]["error"])

    def test_timeout_is_error_and_saved(self):
        result, report = self.run_double("time.sleep(10)\n", timeout=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exceeded", report["cases"][0]["error"])


if __name__ == "__main__":
    unittest.main()
