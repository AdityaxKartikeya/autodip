"""Persistence layer for end-to-end traceability."""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, Any


def init_db(path: str) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tests (
            test_id TEXT PRIMARY KEY,
            captured_at TEXT,
            processed_at TEXT,
            overall_status TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cv_results (
            test_id TEXT PRIMARY KEY,
            payload_json TEXT,
            FOREIGN KEY(test_id) REFERENCES tests(test_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interpretations (
            test_id TEXT,
            analyte TEXT,
            value TEXT,
            status TEXT,
            channel_value INTEGER,
            normal_max INTEGER,
            FOREIGN KEY(test_id) REFERENCES tests(test_id)
        )
        """
    )
    conn.commit()
    conn.close()


def save_result(path: str, input_payload: Dict[str, Any], result_payload: Dict[str, Any]) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO tests(test_id, captured_at, processed_at, overall_status)
        VALUES (?, ?, ?, ?)
        """,
        (
            result_payload["test_id"],
            result_payload.get("captured_at"),
            result_payload.get("processed_at"),
            result_payload.get("overall_status"),
        ),
    )

    cur.execute(
        """
        INSERT OR REPLACE INTO cv_results(test_id, payload_json)
        VALUES (?, ?)
        """,
        (result_payload["test_id"], json.dumps(input_payload)),
    )

    cur.execute("DELETE FROM interpretations WHERE test_id = ?", (result_payload["test_id"],))
    for item in result_payload.get("interpretations", []):
        cur.execute(
            """
            INSERT INTO interpretations(test_id, analyte, value, status, channel_value, normal_max)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result_payload["test_id"],
                item.get("analyte"),
                item.get("value"),
                item.get("status"),
                item.get("channel_value"),
                item.get("normal_max"),
            ),
        )

    conn.commit()
    conn.close()
