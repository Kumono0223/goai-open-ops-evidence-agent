import json
import unittest

from src.goai_agent.agent import run_workflow


class AgentTests(unittest.TestCase):
    def test_workflow_has_evidence_and_human_gate(self):
        result = run_workflow("examples/maintenance.csv")
        self.assertTrue(result["human_review_required"])
        self.assertIn("anomaly", result["evidence"])
        json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()

