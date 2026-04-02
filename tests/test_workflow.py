import unittest

from autodip.workflow import CHARTS, interpret_pad, run_interpretation


class WorkflowTests(unittest.TestCase):
    def test_marks_out_of_range_when_threshold_crosses(self):
        payload = {
            "test_id": "T-1",
            "captured_at": "2026-04-02T00:00:00Z",
            "strip": {
                "pads": [
                    {"index": 1, "analyte": "glucose", "color_rgb": [180, 80, 25]},
                    {"index": 2, "analyte": "protein", "color_rgb": [255, 255, 180]},
                ]
            },
        }

        result = run_interpretation(payload)

        self.assertEqual(result["overall_status"], "attention_needed")
        self.assertEqual(result["interpretations"][0]["status"], "out_of_range")
        self.assertEqual(result["interpretations"][0]["value"], "high")
        self.assertEqual(result["interpretations"][1]["status"], "normal")
        self.assertIn("confidence", result["interpretations"][0])

    def test_reference_colors_map_to_their_own_labels(self):
        # Exact chart colors should map back to their declared label.
        for analyte, chart in CHARTS.items():
            for level in chart.levels:
                out = interpret_pad(analyte, list(level.rgb))
                self.assertEqual(out["value"], level.label, msg=f"{analyte} @ {level.rgb}")

    def test_ph_blue_green_bias_maps_to_alkaline_family(self):
        out = interpret_pad("ph", [82, 142, 126])
        self.assertIn(out["value"], {"high_alkaline", "slightly_alkaline"})


if __name__ == "__main__":
    unittest.main()
