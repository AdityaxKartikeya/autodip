from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

from autodip.cv import extract_cv_payload
from autodip.report import generate_report
from autodip.workflow import run_interpretation
from lab.models import DipTest


def process_dip_test(test: DipTest) -> DipTest:
    payload = extract_cv_payload(test.image.path, test_id=f"DT-{test.id}")
    result = run_interpretation(payload)

    report_rel_path = Path("reports") / f"diptest_{test.id}.pdf"
    report_abs_path = Path(settings.MEDIA_ROOT) / report_rel_path
    report_abs_path.parent.mkdir(parents=True, exist_ok=True)

    generate_report(result, str(report_abs_path))

    test.status = "completed"
    test.result_json = {"input": payload, "output": result}
    test.report_file.save(report_rel_path.name, ContentFile(report_abs_path.read_bytes()), save=False)
    test.save(update_fields=["status", "result_json", "report_file"])

    return test
