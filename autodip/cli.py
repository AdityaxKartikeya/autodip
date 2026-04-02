"""CLI to execute urine diptest automation workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autodip.db import init_db, save_result
from autodip.report import generate_report
from autodip.workflow import run_interpretation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run urine diptest automation workflow")
    parser.add_argument("--input", required=True, help="Path to CV JSON input payload")
    parser.add_argument("--db", default="autodip.sqlite", help="SQLite database path")
    parser.add_argument("--report", default="report.pdf", help="Output report path")
    parser.add_argument("--output", default="result.json", help="Output interpreted JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run_interpretation(payload)

    init_db(args.db)
    save_result(args.db, payload, result)

    report_path = generate_report(result, args.report)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Processed test_id={result.get('test_id')}")
    print(f"Result JSON: {args.output}")
    print(f"Report: {report_path}")
    print(f"Database: {args.db}")


if __name__ == "__main__":
    main()
