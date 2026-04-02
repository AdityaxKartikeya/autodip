import unittest

from autodip.workflow import run_interpretation


class WorkflowTests(unittest.TestCase):
    def test_marks_out_of_range_when_threshold_crosses(self):
        payload = {
            "test_id": "T-1",
            "captured_at": "2026-04-02T00:00:00Z",
            "strip": {
                "pads": [
                    {"index": 1, "analyte": "glucose", "color_rgb": [200, 10, 10]},
                    {"index": 2, "analyte": "protein", "color_rgb": [10, 100, 10]},
                ]
            },
        }

        result = run_interpretation(payload)

        self.assertEqual(result["overall_status"], "attention_needed")
        self.assertEqual(result["interpretations"][0]["status"], "out_of_range")
        self.assertEqual(result["interpretations"][1]["status"], "normal")
        self.assertIn("signal", result["interpretations"][0])


if __name__ == "__main__":
    unittest.main()
