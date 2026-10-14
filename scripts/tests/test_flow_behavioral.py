"""Negative controls for flow evidence and the two repaired smoke graders."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("flow_cases", ROOT / "scripts/behavioral/cases.py")
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)


class FlowBehavioralTests(unittest.TestCase):
    def prepare(self, name, directory):
        workspace = Path(directory) / "workspace"
        workspace.mkdir()
        _, before, _ = cases.prepare(ROOT, name, workspace)
        self.assertFalse(any("evals/" in p for p in before))
        return before

    def test_design_scope_mentions_are_not_token_adoption(self):
        with tempfile.TemporaryDirectory() as directory:
            before = self.prepare("design-existing", directory)
            target = "apps/dashboard/DESIGN_SYSTEM.md"
            addition = '\n## Decisions Log\nsrc/theme.css: --accent --surface --ink\n'
            for note in ("Workspace root uses #e26050; it does not apply to this dashboard.",
                         "앱 강조색 #175cd3는 루트 #e26050와 다르며 루트 값을 적용하지 않는다."):
                after = {**before, target: before[target] + (addition + note).encode()}
                self.assertTrue(all(c["passed"] for c in cases.grade("design-existing", before, after)), note)
            for assignment in ("--accent: #e26050;", "| accent | `#e26050` |", "| #e26050 | --accent |"):
                after = {**before, target: before[target] + (addition + assignment).encode()}
                self.assertFalse(all(c["passed"] for c in cases.grade("design-existing", before, after)), assignment)

    def test_review_consumer_name_cannot_stand_in_for_domain_trace(self):
        finding = {"file": "src/api/toInvoice.ts", "line": 9,
                   "description": "archived enters InvoiceStatusLabel", "fix": "add archived labels"}
        report = {"findings": [finding], "tests_executed": False, "limitations": "snapshot only"}
        def results():
            return {c["check"]: c["passed"] for c in cases.grade("review-runtime", {},
                {"review.json": json.dumps(report).encode()})}
        self.assertFalse(results()["cross_file_contract_traced"])
        finding["description"] = "archived escapes src/domain/invoice.ts and reaches InvoiceStatusLabel"
        self.assertTrue(all(results().values()))
        report["findings"].append(dict(finding))
        self.assertFalse(results()["one_causal_finding"])

    def test_flow_inputs_preserve_actual_prd_and_exclude_rubrics(self):
        with tempfile.TemporaryDirectory() as directory:
            before = self.prepare("flow-from-prd", directory)
            self.assertEqual(before["prd.md"], (ROOT / "reports/prd-write-2026-10-04/prd-from-problem/prd.md").read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            before = self.prepare("flow-design", directory)
            self.assertEqual(before["prd.md"], (ROOT / "reports/prd-gate-host-proof-2026-10-06/product-chain/published/prd.md").read_bytes())
            self.assertIn(".eval-plugins/design/skills/prototype-explore/SKILL.md", before)

    def test_update_rejects_id_loss_unrelated_edits_and_metadata_only_change(self):
        with tempfile.TemporaryDirectory() as directory:
            before = self.prepare("flow-update", directory)
            old = before["existing-flow.md"].decode()
            new = old.replace("revision: 2", "revision: 3").replace(
                "The user may select another tag.", "Keep the selected tag; retry it only on explicit action, never automatically. The user may select another tag.")
            def passed(value, extra=None):
                return all(c["passed"] for c in cases.grade("flow-update", before,
                    {**before, "existing-flow.md": value.encode(), **(extra or {})}))
            self.assertTrue(passed(new))
            self.assertFalse(passed(new.replace("FLOW-002", "FLOW-099")))
            self.assertFalse(passed(new.replace("remains tentative", "is final")))
            self.assertFalse(passed(new, {"requirements.md": b"rewritten source"}))
            self.assertFalse(passed(old.replace("revision: 2", "revision: 3")))

    def test_design_chain_cannot_rewrite_existing_files_in_output_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            before = self.prepare("flow-design", directory)
            before["explore/user-note.md"] = b"existing user note"
            after = {**before, "explore/user-note.md": b"rewritten"}
            result = cases.grade("flow-design", before, after)
            self.assertFalse(next(c["passed"] for c in result if c["check"] == "only_requested_output_changed"))


if __name__ == "__main__":
    unittest.main()
