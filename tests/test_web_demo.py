from pathlib import Path
import unittest


class WebDemoTests(unittest.TestCase):
    def setUp(self):
        self.html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")

    def test_demo_is_self_contained_and_truthful(self):
        for marker in (
            "Open Ops Evidence Agent",
            "数据只在浏览器本地处理",
            "不会自动停机、派单或修改生产系统",
            "下载 JSON 证据包",
            "human_approval_required",
        ):
            self.assertIn(marker, self.html)
        self.assertNotIn("<script src=", self.html)
        self.assertNotIn("<link rel=\"stylesheet\"", self.html)
        self.assertNotIn("fetch(", self.html)
        self.assertNotIn("XMLHttpRequest", self.html)

    def test_demo_exposes_versioned_evidence_contract(self):
        for marker in (
            "2026.08-evidence-v2",
            "ops-review-policy-1.0",
            "input_evidence",
            "evidence_id",
            "incident_id",
            "production_actions_executed:false",
        ):
            self.assertIn(marker, self.html)


if __name__ == "__main__":
    unittest.main()
