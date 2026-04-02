"""Simple CV extraction from a dip-strip image.

This initial implementation assumes a near-vertical strip and divides the center
region into 10 pad zones, then computes mean RGB for each zone.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

ANALYTES = [
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


def _avg_rgb(img: Image.Image, box: tuple[int, int, int, int]) -> List[int]:
    crop = img.crop(box).convert("RGB")
    pixels = list(crop.getdata())
    count = max(len(pixels), 1)
    r = sum(p[0] for p in pixels) // count
    g = sum(p[1] for p in pixels) // count
    b = sum(p[2] for p in pixels) // count
    return [r, g, b]


def extract_cv_payload(image_path: str, test_id: str) -> Dict[str, Any]:
    img = Image.open(Path(image_path))
    width, height = img.size

    # Heuristic: strip expected around center area.
    strip_x1 = int(width * 0.40)
    strip_x2 = int(width * 0.60)
    strip_y1 = int(height * 0.10)
    strip_y2 = int(height * 0.90)

    strip_height = strip_y2 - strip_y1
    pad_height = strip_height // 10

    pads = []
    for idx in range(10):
        y1 = strip_y1 + idx * pad_height
        y2 = strip_y1 + (idx + 1) * pad_height if idx < 9 else strip_y2
        box = (strip_x1, y1, strip_x2, y2)
        rgb = _avg_rgb(img, box)
        pads.append(
            {
                "index": idx + 1,
                "analyte": ANALYTES[idx],
                "bbox": {"x": strip_x1, "y": y1, "w": strip_x2 - strip_x1, "h": y2 - y1},
                "color_rgb": rgb,
            }
        )

    return {
        "test_id": test_id,
        "captured_at": None,
        "strip": {
            "pad_count": 10,
            "pads": pads,
        },
    }
