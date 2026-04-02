"""Core workflow for urine dip test automation.

This module converts CV pad colors into analyte interpretations with
per-analyte calibration and scale-aware outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(frozen=True)
class AnalyteRule:
    name: str
    mode: str
    # For binary/ordinal style pads.
    positive_threshold: float | None = None
    high_threshold: float | None = None
    trace_threshold: float | None = None
    # For scale-based pads.
    scale_breaks: tuple[float, ...] = ()
    scale_labels: tuple[str, ...] = ()


ANALYTE_RULES: Dict[str, AnalyteRule] = {
    "glucose": AnalyteRule("glucose", "ordinal", positive_threshold=0.26, high_threshold=0.38),
    "protein": AnalyteRule("protein", "binary", positive_threshold=0.75),
    "ketone": AnalyteRule("ketone", "ordinal", positive_threshold=0.25, high_threshold=0.36),
    "blood": AnalyteRule("blood", "binary", positive_threshold=0.20),
    "nitrite": AnalyteRule("nitrite", "binary", positive_threshold=0.18),
    "leukocytes": AnalyteRule("leukocytes", "trace", trace_threshold=0.10, positive_threshold=0.20),
    "bilirubin": AnalyteRule("bilirubin", "binary", positive_threshold=0.22),
    "urobilinogen": AnalyteRule("urobilinogen", "ordinal", positive_threshold=0.20, high_threshold=0.32),
    # scale labels correspond to <=break[0], <=break[1], >break[1]
    "ph": AnalyteRule("ph", "scale", scale_breaks=(0.33, 0.66), scale_labels=("acidic", "neutral", "alkaline")),
    # low/normal/high SG
    "specific_gravity": AnalyteRule(
        "specific_gravity",
        "scale",
        scale_breaks=(0.35, 0.70),
        scale_labels=("low (1.005)", "normal (1.010-1.020)", "high (1.025+)"),
    ),
}


def _normalized_features(rgb: List[int]) -> Dict[str, float]:
    r, g, b = [max(0, min(255, int(v))) for v in rgb]
    total = max(r + g + b, 1)
    maxc = max(r, g, b)
    minc = min(r, g, b)
    chroma = maxc - minc
    # Chroma ratio captures pad color intensity regardless of brightness.
    intensity = chroma / max(maxc, 1)

    # Dominance score identifies "chemical color shift" rather than brightness.
    dominant_channel = max((r, "r"), (g, "g"), (b, "b"))[1]
    dominant_value = {"r": r, "g": g, "b": b}[dominant_channel]
    others = [v for c, v in (("r", r), ("g", g), ("b", b)) if c != dominant_channel]
    dominance = (dominant_value - sum(others) / 2.0) / 255.0

    # Hue-like metric in [0,1]. Good enough for coarse pH/SG scale bins.
    if chroma == 0:
        hue = 0.0
    elif maxc == r:
        hue = ((g - b) / chroma) % 6
    elif maxc == g:
        hue = (b - r) / chroma + 2
    else:
        hue = (r - g) / chroma + 4
    hue /= 6.0

    return {
        "r_ratio": r / total,
        "g_ratio": g / total,
        "b_ratio": b / total,
        "dominance": max(0.0, dominance),
        "intensity": intensity,
        "hue": hue,
    }


def _signal_strength(analyte: str, feats: Dict[str, float]) -> float:
    # Per-analyte weighting to avoid one-channel brightness bias.
    if analyte in {"glucose", "blood", "bilirubin"}:
        return 0.55 * feats["r_ratio"] + 0.25 * feats["dominance"] + 0.20 * feats["intensity"]
    if analyte in {"protein", "nitrite", "urobilinogen"}:
        return 0.55 * feats["g_ratio"] + 0.25 * feats["dominance"] + 0.20 * feats["intensity"]
    if analyte in {"ketone", "leukocytes"}:
        return 0.55 * feats["b_ratio"] + 0.25 * feats["dominance"] + 0.20 * feats["intensity"]
    if analyte == "ph":
        return feats["hue"]
    if analyte == "specific_gravity":
        # SG tends to shift saturation/chroma more than pure hue.
        return 0.6 * feats["intensity"] + 0.4 * feats["hue"]
    return feats["intensity"]


def interpret_pad(analyte: str, rgb: List[int]) -> Dict[str, Any]:
    rule = ANALYTE_RULES.get(analyte)
    if rule is None:
        return {
            "analyte": analyte,
            "value": "unknown",
            "status": "requires_review",
            "reason": "no_rule_configured",
        }

    feats = _normalized_features(rgb)
    signal = _signal_strength(analyte, feats)

    if rule.mode == "binary":
        is_positive = signal >= float(rule.positive_threshold)
        return {
            "analyte": analyte,
            "signal": round(signal, 4),
            "value": "positive" if is_positive else "negative",
            "status": "out_of_range" if is_positive else "normal",
        }

    if rule.mode == "ordinal":
        if signal >= float(rule.high_threshold):
            return {"analyte": analyte, "signal": round(signal, 4), "value": "positive_high", "status": "out_of_range"}
        if signal >= float(rule.positive_threshold):
            return {"analyte": analyte, "signal": round(signal, 4), "value": "positive", "status": "out_of_range"}
        return {"analyte": analyte, "signal": round(signal, 4), "value": "negative", "status": "normal"}

    if rule.mode == "trace":
        if signal >= float(rule.positive_threshold):
            return {"analyte": analyte, "signal": round(signal, 4), "value": "positive", "status": "out_of_range"}
        if signal >= float(rule.trace_threshold):
            return {"analyte": analyte, "signal": round(signal, 4), "value": "trace_positive", "status": "borderline"}
        return {"analyte": analyte, "signal": round(signal, 4), "value": "negative", "status": "normal"}

    if rule.mode == "scale":
        low_cut, high_cut = rule.scale_breaks
        if signal <= low_cut:
            value = rule.scale_labels[0]
        elif signal <= high_cut:
            value = rule.scale_labels[1]
        else:
            value = rule.scale_labels[2]

        status = "normal" if "normal" in value or value == "neutral" else "out_of_range"
        return {"analyte": analyte, "signal": round(signal, 4), "value": value, "status": status}

    return {
        "analyte": analyte,
        "signal": round(signal, 4),
        "value": "unknown",
        "status": "requires_review",
        "reason": f"unsupported_mode={rule.mode}",
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
