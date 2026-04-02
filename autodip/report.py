"""Report generation utilities.

Currently emits a text-based report placeholder at a .pdf path.
Integrate with real PDF rendering engine in production.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any


def generate_report(result_payload: Dict[str, Any], output_path: str, branding: str = "AutoDip Diagnostics") -> str:
    path = Path(output_path)
    lines = [
        f"Brand: {branding}",
        f"Test ID: {result_payload.get('test_id')}",
        f"Captured At: {result_payload.get('captured_at')}",
        f"Processed At: {result_payload.get('processed_at')}",
        f"Overall Status: {result_payload.get('overall_status')}",
        "",
        "Analyte Results:",
    ]

    for item in result_payload.get("interpretations", []):
        lines.append(
            f"- {item.get('analyte')}: {item.get('value')} "
            f"(status={item.get('status')}, channel_value={item.get('channel_value')}, normal_max={item.get('normal_max')})"
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
