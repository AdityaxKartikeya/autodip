"""Core workflow for urine dip test automation.

This is an implementation scaffold that turns pad color/position payloads into
interpreted results and a persistable result bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Any


@dataclass(frozen=True)
class AnalyteRule:
    name: str
    channel: str
    normal_max: int


# Simple thresholding rules for demonstration (replace with calibrated chart lookup).
ANALYTE_RULES: List[AnalyteRule] = [
    AnalyteRule("glucose", "r", 120),
    AnalyteRule("protein", "g", 130),
    AnalyteRule("ketone", "b", 110),
    AnalyteRule("blood", "r", 140),
    AnalyteRule("nitrite", "g", 125),
    AnalyteRule("leukocytes", "b", 130),
    AnalyteRule("bilirubin", "r", 115),
    AnalyteRule("urobilinogen", "g", 140),
    AnalyteRule("ph", "b", 150),
    AnalyteRule("specific_gravity", "r", 160),
]


def _channel_value(rgb: List[int], channel: str) -> int:
    mapping = {"r": 0, "g": 1, "b": 2}
    return rgb[mapping[channel]]


def interpret_pad(analyte: str, rgb: List[int]) -> Dict[str, Any]:
    rule = next((r for r in ANALYTE_RULES if r.name == analyte), None)
    if rule is None:
        return {
            "analyte": analyte,
            "value": "unknown",
            "status": "requires_review",
            "reason": "no_rule_configured",
        }

    value = _channel_value(rgb, rule.channel)
    status = "normal" if value <= rule.normal_max else "out_of_range"
    severity = "negative" if value <= rule.normal_max else "positive"

    return {
        "analyte": analyte,
        "channel": rule.channel,
        "channel_value": value,
        "normal_max": rule.normal_max,
        "value": severity,
        "status": status,
    }


def run_interpretation(payload: Dict[str, Any]) -> Dict[str, Any]:
    pads = payload.get("strip", {}).get("pads", [])

    interpretations = []
    for pad in pads:
        analyte = pad.get("analyte", f"pad_{pad.get('index', 'x')}")
        rgb = pad.get("color_rgb", [0, 0, 0])
        result = interpret_pad(analyte, rgb)
        result["index"] = pad.get("index")
        result["bbox"] = pad.get("bbox")
        interpretations.append(result)

    overall_status = "normal"
    if any(item.get("status") == "out_of_range" for item in interpretations):
        overall_status = "attention_needed"

    return {
        "test_id": payload.get("test_id"),
        "captured_at": payload.get("captured_at"),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "interpretations": interpretations,
    }
