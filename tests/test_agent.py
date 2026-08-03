import json
import tempfile
import unittest
from pathlib import Path

from src.goai_agent.agent import METHOD_VERSION, ReviewPolicy, render_markdown, run_workflow


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.report = run_workflow("examples/maintenance.csv")

    def test_workflow_has_versioned_input_evidence(self):
        self.assertEqual(self.report["methodology_version"], METHOD_VERSION)
        self.assertEqual(len(self.report["input_evidence"]["sha256"]), 64)
        self.assertEqual(self.report["input_evidence"]["rows"], 9)
        self.assertEqual(self.report["input_evidence"]["data_quality_issues"], [])

    def test_anomaly_becomes_proposed_incident_with_human_gate(self):
        self.assertEqual(self.report["priority_machines"], ["M-02"])
        incident = self.report["incidents"][0]
        self.assertEqual(incident["severity"], "critical")
        self.assertEqual(incident["state"], "proposed")
        self.assertEqual(incident["decision"], "human_approval_required")
        self.assertFalse(self.report["production_actions_executed"])
        self.assertTrue(self.report["human_review_required"])

    def test_report_is_deterministic(self):
        again = run_workflow("examples/maintenance.csv")
        self.assertEqual(self.report, again)
        json.dumps(self.report, ensure_ascii=False)

    def test_policy_threshold_changes_detection(self):
        strict = run_workflow("examples/maintenance.csv", policy=ReviewPolicy(z_threshold=4.0))
        self.assertEqual(strict["incidents"], [])
        self.assertEqual(strict["policy"]["z_threshold"], 4.0)

    def test_missing_required_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("date,machine,value\n2026-08-03,M-01,1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                run_workflow(path)

    def test_markdown_contains_trace_and_safety_boundary(self):
        markdown = render_markdown(self.report)
        self.assertIn(self.report["input_evidence"]["sha256"], markdown)
        self.assertIn(self.report["incidents"][0]["incident_id"], markdown)
        self.assertIn("Production actions executed: **No**", markdown)


if __name__ == "__main__":
    unittest.main()
