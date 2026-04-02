"""Report generation utilities.

Generates a real single-page PDF without external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(lines: List[str]) -> bytes:
    content_lines = ["BT", "/F1 11 Tf", "40 800 Td", "14 TL"]
    for idx, line in enumerate(lines):
        if idx > 0:
            content_lines.append("T*")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: List[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"\nendstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def generate_report(result_payload: Dict[str, Any], output_path: str, branding: str = "AutoDip Diagnostics") -> str:
    path = Path(output_path)
    lines = [
        branding,
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
            f"(measured={item.get('measured_value')}, status={item.get('status')}, confidence={item.get('confidence')})"
        )

    path.write_bytes(_build_simple_pdf(lines))
    return str(path)
