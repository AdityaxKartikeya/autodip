"""Core workflow for urine dip test automation.

This module interprets pad colors using a reference color chart for each analyte.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import sqrt
from typing import Any, Dict, List, Sequence


@dataclass(frozen=True)
class ReferenceLevel:
    label: str
    measured_value: str
    rgb: tuple[int, int, int]
    status: str


@dataclass(frozen=True)
class AnalyteChart:
    name: str
    levels: Sequence[ReferenceLevel]
    clinical_note: str


CHARTS: Dict[str, AnalyteChart] = {
    "glucose": AnalyteChart(
        name="glucose",
        clinical_note="Possible Diabetes Mellitus when persistently elevated.",
        levels=(
            ReferenceLevel("negative", "0 mg/dL", (245, 222, 179), "normal"),
            ReferenceLevel("trace", "50-100 mg/dL", (235, 200, 120), "borderline"),
            ReferenceLevel("slightly_high", "100 mg/dL", (220, 170, 60), "out_of_range"),
            ReferenceLevel("moderate", "250 mg/dL", (205, 120, 40), "out_of_range"),
            ReferenceLevel("high", "500 mg/dL", (180, 80, 25), "out_of_range"),
            ReferenceLevel("very_high", ">=1000 mg/dL", (145, 45, 15), "out_of_range"),
        ),
    ),
    "protein": AnalyteChart(
        name="protein",
        clinical_note="Persistent protein elevation may indicate kidney stress.",
        levels=(
            ReferenceLevel("negative", "0 mg/dL", (255, 255, 180), "normal"),
            ReferenceLevel("trace", "10-20 mg/dL", (240, 230, 140), "borderline"),
            ReferenceLevel("slightly_high", "30 mg/dL", (200, 180, 90), "out_of_range"),
            ReferenceLevel("moderate", "100 mg/dL", (160, 140, 80), "out_of_range"),
            ReferenceLevel("high", "300 mg/dL", (120, 110, 70), "out_of_range"),
            ReferenceLevel("very_high", ">=1000 mg/dL", (80, 90, 60), "out_of_range"),
        ),
    ),
    "ketone": AnalyteChart(
        name="ketone",
        clinical_note="Can be seen in fasting, diabetes, or ketogenic diets.",
        levels=(
            ReferenceLevel("negative", "0 mg/dL", (255, 235, 215), "normal"),
            ReferenceLevel("trace", "5 mg/dL", (245, 180, 160), "borderline"),
            ReferenceLevel("slightly_high", "15 mg/dL", (230, 120, 140), "out_of_range"),
            ReferenceLevel("moderate", "40 mg/dL", (200, 80, 120), "out_of_range"),
            ReferenceLevel("high", "80 mg/dL", (150, 40, 110), "out_of_range"),
            ReferenceLevel("very_high", "160 mg/dL", (110, 20, 90), "out_of_range"),
        ),
    ),
    "blood": AnalyteChart(
        name="blood",
        clinical_note="May indicate stones, infection, trauma, or other urinary pathology.",
        levels=(
            ReferenceLevel("negative", "0 RBC/uL", (255, 255, 170), "normal"),
            ReferenceLevel("trace", "5-10 RBC/uL", (220, 200, 120), "borderline"),
            ReferenceLevel("slightly_high", "25 RBC/uL", (180, 160, 90), "out_of_range"),
            ReferenceLevel("moderate", "50 RBC/uL", (150, 130, 70), "out_of_range"),
            ReferenceLevel("high", "250 RBC/uL", (120, 100, 60), "out_of_range"),
        ),
    ),
    "nitrite": AnalyteChart(
        name="nitrite",
        clinical_note="Positive nitrite strongly suggests bacteriuria/UTI.",
        levels=(
            ReferenceLevel("negative", "none", (255, 240, 180), "normal"),
            ReferenceLevel("positive", "bacteria present", (210, 90, 140), "out_of_range"),
        ),
    ),
    "leukocytes": AnalyteChart(
        name="leukocytes",
        clinical_note="Leukocytes indicate inflammatory or infectious immune response.",
        levels=(
            ReferenceLevel("negative", "0 WBC/uL", (255, 250, 200), "normal"),
            ReferenceLevel("trace", "15 WBC/uL", (230, 220, 160), "borderline"),
            ReferenceLevel("slightly_high", "70 WBC/uL", (200, 180, 140), "out_of_range"),
            ReferenceLevel("moderate", "125 WBC/uL", (170, 140, 130), "out_of_range"),
            ReferenceLevel("high", "500 WBC/uL", (140, 100, 120), "out_of_range"),
            ReferenceLevel("very_high", "500+ WBC/uL", (110, 70, 110), "out_of_range"),
        ),
    ),
    "bilirubin": AnalyteChart(
        name="bilirubin",
        clinical_note="Elevated bilirubin may suggest hepatobiliary disease.",
        levels=(
            ReferenceLevel("negative", "0 mg/dL", (255, 245, 180), "normal"),
            ReferenceLevel("slightly_high", "0.5 mg/dL", (230, 200, 100), "out_of_range"),
            ReferenceLevel("moderate", "1 mg/dL", (200, 150, 60), "out_of_range"),
            ReferenceLevel("high", "2 mg/dL", (170, 110, 40), "out_of_range"),
            ReferenceLevel("very_high", "4 mg/dL", (140, 80, 20), "out_of_range"),
        ),
    ),
    "urobilinogen": AnalyteChart(
        name="urobilinogen",
        clinical_note="Higher levels may indicate liver dysfunction or hemolysis.",
        levels=(
            ReferenceLevel("normal", "0.2 mg/dL", (255, 230, 170), "normal"),
            ReferenceLevel("slightly_high", "1 mg/dL", (230, 180, 120), "out_of_range"),
            ReferenceLevel("moderate", "2 mg/dL", (210, 140, 80), "out_of_range"),
            ReferenceLevel("high", "4 mg/dL", (180, 100, 60), "out_of_range"),
            ReferenceLevel("very_high", "8 mg/dL", (150, 70, 40), "out_of_range"),
        ),
    ),
    "ph": AnalyteChart(
        name="ph",
        clinical_note="Urinary pH varies by hydration, diet, and metabolic state.",
        levels=(
            ReferenceLevel("low_acidic", "pH 5.0", (240, 160, 60), "out_of_range"),
            ReferenceLevel("slightly_acidic", "pH 5.5", (230, 180, 80), "borderline"),
            ReferenceLevel("normal", "pH 6.0", (210, 190, 90), "normal"),
            ReferenceLevel("normal", "pH 6.5", (180, 200, 100), "normal"),
            ReferenceLevel("normal", "pH 7.0", (140, 180, 90), "normal"),
            ReferenceLevel("slightly_alkaline", "pH 7.5", (110, 160, 100), "borderline"),
            ReferenceLevel("high_alkaline", "pH 8.0", (80, 140, 120), "out_of_range"),
            ReferenceLevel("high_alkaline", "pH 8.5", (70, 120, 140), "out_of_range"),
            ReferenceLevel("high_alkaline", "pH 9.0", (60, 100, 160), "out_of_range"),
        ),
    ),
    "specific_gravity": AnalyteChart(
        name="specific_gravity",
        clinical_note="Specific gravity reflects hydration and renal concentrating capacity.",
        levels=(
            ReferenceLevel("low", "1.005", (255, 240, 200), "out_of_range"),
            ReferenceLevel("slightly_low", "1.010", (240, 220, 170), "borderline"),
            ReferenceLevel("normal", "1.015", (225, 200, 140), "normal"),
            ReferenceLevel("normal", "1.020", (210, 180, 120), "normal"),
            ReferenceLevel("slightly_high", "1.025", (190, 160, 100), "borderline"),
            ReferenceLevel("high", "1.030", (170, 140, 80), "out_of_range"),
        ),
    ),
}


def _chroma(rgb: Sequence[int]) -> tuple[float, float, float]:
    r, g, b = [max(0, min(255, int(v))) for v in rgb]
    total = max(r + g + b, 1)
    return r / total, g / total, b / total


def _distance_rgb(sample: Sequence[int], target: Sequence[int]) -> float:
    sr, sg, sb = [float(v) for v in sample]
    tr, tg, tb = [float(v) for v in target]
    raw = sqrt((sr - tr) ** 2 + (sg - tg) ** 2 + (sb - tb) ** 2)

    sc = _chroma(sample)
    tc = _chroma(target)
    chroma = sqrt((sc[0] - tc[0]) ** 2 + (sc[1] - tc[1]) ** 2 + (sc[2] - tc[2]) ** 2) * 255.0
    # Blend raw distance + normalized chroma distance for better brightness robustness.
    return 0.6 * raw + 0.4 * chroma


def interpret_pad(analyte: str, rgb: List[int]) -> Dict[str, Any]:
    chart = CHARTS.get(analyte)
    if chart is None:
        return {
            "analyte": analyte,
            "value": "unknown",
            "status": "requires_review",
            "reason": "no_chart_configured",
        }

    ranked = sorted(
        (
            {
                "level": level,
                "distance": _distance_rgb(rgb, level.rgb),
            }
            for level in chart.levels
        ),
        key=lambda x: x["distance"],
    )
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else ranked[0]

    confidence = max(0.0, min(1.0, 1.0 - (best["distance"] / 220.0)))
    ambiguous = (second["distance"] - best["distance"]) < 8.0

    best_level = best["level"]
    status = "borderline" if ambiguous and best_level.status == "normal" else best_level.status

    return {
        "analyte": analyte,
        "value": best_level.label,
        "measured_value": best_level.measured_value,
        "status": status,
        "confidence": round(confidence, 4),
        "distance": round(best["distance"], 3),
        "clinical_note": chart.clinical_note,
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
        result["color_rgb"] = rgb
        interpretations.append(result)

    overall_status = "normal"
    if any(item.get("status") in {"out_of_range", "borderline"} for item in interpretations):
        overall_status = "attention_needed"

    return {
        "test_id": payload.get("test_id"),
        "captured_at": payload.get("captured_at"),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "interpretations": interpretations,
    }
