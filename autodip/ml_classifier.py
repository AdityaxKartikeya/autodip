"""Small scikit-learn classifiers for urine dipstick pad interpretation.

Design:
- One model per analyte.
- Input feature vector includes RGB, HSV, color ratios, brightness.
- Supports random_forest, svm, logistic_regression.

Example sample:
{
  "analyte": "glucose",
  "rgb": [245, 222, 179],
  "label": "negative"
}
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Dict, Iterable, List, Literal, Sequence
import colorsys
import json

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC


AnalyteName = Literal[
    "glucose",
    "protein",
    "ketone",
    "blood",
    "nitrite",
    "leukocytes",
    "bilirubin",
    "urobilinogen",
    "ph",
    "specific_gravity",
]

AlgorithmName = Literal["random_forest", "svm", "logistic_regression"]


@dataclass
class AnalyteModel:
    analyte: str
    model: Any
    encoder: LabelEncoder
    labels: List[str]


def rgb_to_hsv(rgb: Sequence[int]) -> tuple[float, float, float]:
    """Convert RGB 0-255 to HSV in [0,1] range."""
    r, g, b = [max(0, min(255, int(v))) / 255.0 for v in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def _safe_ratio(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0


def extract_features(rgb: Sequence[int]) -> np.ndarray:
    """Feature vector: R,G,B,H,S,V,R/G,R/B,G/B,brightness."""
    r, g, b = [float(max(0, min(255, int(v)))) for v in rgb]
    h, s, v = rgb_to_hsv((int(r), int(g), int(b)))

    rg = _safe_ratio(r, g)
    rb = _safe_ratio(r, b)
    gb = _safe_ratio(g, b)
    brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b

    return np.array([r, g, b, h, s, v, rg, rb, gb, brightness], dtype=np.float32)


def _build_estimator(algorithm: AlgorithmName) -> Any:
    if algorithm == "random_forest":
        return RandomForestClassifier(n_estimators=200, random_state=42, min_samples_leaf=1)
    if algorithm == "svm":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", SVC(kernel="rbf", C=2.0, gamma="scale", probability=True, random_state=42)),
            ]
        )
    if algorithm == "logistic_regression":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=2000, multi_class="auto", random_state=42)),
            ]
        )
    raise ValueError(f"Unsupported algorithm: {algorithm}")


def train_analyte_models(
    samples: List[Dict[str, Any]],
    algorithm: AlgorithmName = "random_forest",
) -> Dict[str, AnalyteModel]:
    """Train one classifier per analyte.

    samples format:
    [{"analyte":"glucose", "rgb":[245,222,179], "label":"negative"}, ...]
    """
    by_analyte: Dict[str, List[Dict[str, Any]]] = {}
    for row in samples:
        analyte = str(row["analyte"])
        by_analyte.setdefault(analyte, []).append(row)

    models: Dict[str, AnalyteModel] = {}
    for analyte, rows in by_analyte.items():
        X = np.vstack([extract_features(row["rgb"]) for row in rows])
        y_raw = [str(row["label"]) for row in rows]

        enc = LabelEncoder()
        y = enc.fit_transform(y_raw)
        estimator = _build_estimator(algorithm)
        estimator.fit(X, y)

        models[analyte] = AnalyteModel(
            analyte=analyte,
            model=estimator,
            encoder=enc,
            labels=list(enc.classes_),
        )

    return models


def evaluate_models(
    samples: List[Dict[str, Any]],
    algorithm: AlgorithmName = "random_forest",
    test_size: float = 0.25,
) -> Dict[str, Dict[str, Any]]:
    """Train/evaluate per analyte and return metrics incl. confusion matrix."""
    results: Dict[str, Dict[str, Any]] = {}

    by_analyte: Dict[str, List[Dict[str, Any]]] = {}
    for row in samples:
        by_analyte.setdefault(str(row["analyte"]), []).append(row)

    for analyte, rows in by_analyte.items():
        X = np.vstack([extract_features(row["rgb"]) for row in rows])
        y_raw = np.array([str(row["label"]) for row in rows])

        if len(rows) < 8:
            raise ValueError(f"Need at least 8 samples for analyte '{analyte}' to evaluate reliably.")

        unique_labels, counts = np.unique(y_raw, return_counts=True)
        can_stratify = bool(len(unique_labels) > 1 and np.min(counts) >= 2)

        if can_stratify:
            X_train, X_test, y_train_raw, y_test_raw = train_test_split(
                X,
                y_raw,
                test_size=test_size,
                random_state=42,
                stratify=y_raw,
            )
            eval_mode = "holdout"
        else:
            # Tiny datasets: fit/evaluate on full set (diagnostic-only metric).
            X_train, y_train_raw = X, y_raw
            X_test, y_test_raw = X, y_raw
            eval_mode = "resubstitution"

        enc = LabelEncoder()
        y_train = enc.fit_transform(y_train_raw)
        y_test = enc.transform(y_test_raw)

        estimator = _build_estimator(algorithm)
        estimator.fit(X_train, y_train)
        y_pred = estimator.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        cm = confusion_matrix(y_test, y_pred, labels=np.arange(len(enc.classes_))).tolist()

        results[analyte] = {
            "accuracy": round(acc, 4),
            "labels": list(enc.classes_),
            "confusion_matrix": cm,
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "eval_mode": eval_mode,
        }

    return results


def predict_level(models: Dict[str, AnalyteModel], analyte: str, rgb: Sequence[int]) -> Dict[str, Any]:
    """Predict class + confidence for a new RGB sample."""
    if analyte not in models:
        raise KeyError(f"No trained model for analyte '{analyte}'")

    item = models[analyte]
    feats = extract_features(rgb).reshape(1, -1)

    probs = item.model.predict_proba(feats)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = item.encoder.inverse_transform([pred_idx])[0]
    confidence = float(probs[pred_idx])

    # normalize any numerical edge case
    confidence = confidence if isfinite(confidence) else 0.0

    return {
        "analyte": analyte,
        "rgb": [int(v) for v in rgb],
        "predicted_label": str(pred_label),
        "confidence": round(confidence, 4),
        "class_probabilities": {
            str(lbl): round(float(prob), 4) for lbl, prob in zip(item.encoder.classes_, probs)
        },
    }


def load_samples_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Training data file must contain a list of samples")
    return data


def demo_train_and_predict(path: str, algorithm: AlgorithmName = "random_forest") -> None:
    """Simple runnable demo for CLI/testing."""
    samples = load_samples_from_json(path)
    metrics = evaluate_models(samples, algorithm=algorithm)
    print("=== Evaluation ===")
    for analyte, m in metrics.items():
        print(f"{analyte:16} acc={m['accuracy']:.3f} n_train={m['n_train']} n_test={m['n_test']}")
        print(f"labels={m['labels']}")
        print(f"cm={m['confusion_matrix']}")

    models = train_analyte_models(samples, algorithm=algorithm)
    print("\n=== Example prediction ===")
    print(predict_level(models, "glucose", [211, 134, 165]))


if __name__ == "__main__":
    # Example:
    # python -m autodip.ml_classifier sample_training_data.json
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m autodip.ml_classifier <training_data.json> [algorithm]")
    algo = str(sys.argv[2]) if len(sys.argv) > 2 else "random_forest"
    demo_train_and_predict(sys.argv[1], algorithm=algo)  # type: ignore[arg-type]
