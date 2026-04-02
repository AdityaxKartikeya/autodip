# Urine Dip Test Automation Process (Computer Vision)

This document translates the handwritten workflow in the image into a complete, implementation-ready process.

## 1) Controlled Capture Setup

1. Place the urine dip strip inside an **opaque imaging box**.
2. Use **stable, uniform lighting** (fixed color temperature and intensity).
3. Keep camera at a **fixed top-down position** (same height and angle for every capture).
4. Include a **reference area** in the scene where possible (white/gray calibration patch) to reduce lighting drift.

## 2) Image Acquisition

1. Capture the image from the top once the strip is ready.
2. Assign a **unique test ID** immediately at capture time.
3. Save raw image with metadata:
   - test_id
   - timestamp
   - device/camera ID
   - operator or instrument ID
   - batch/lot information (if applicable)

## 3) Computer Vision Processing

1. Preprocess image:
   - geometric correction (rotation/perspective)
   - white balance / color normalization
   - denoising
2. Detect strip region and segment all reagent pads.
3. Extract pad-wise features:
   - pad position (x, y, width, height)
   - representative color values (RGB/HSV/Lab)
   - color gradient or intensity statistics
4. Generate a structured machine output (JSON) containing **color + position** data for each pad.

### Example JSON payload

```json
{
  "test_id": "UDT-2026-000123",
  "captured_at": "2026-04-02T10:30:00Z",
  "strip": {
    "pad_count": 10,
    "pads": [
      {
        "index": 1,
        "analyte": "glucose",
        "bbox": {"x": 120, "y": 80, "w": 42, "h": 25},
        "color_rgb": [185, 150, 98],
        "color_hsv": [30, 47, 73],
        "quality_score": 0.98
      }
    ]
  }
}
```

## 4) Clinical Interpretation Layer

1. Compare each pad's measured color profile against the strip manufacturer's **reference color chart**.
2. Convert color match to a **semi-quantitative or categorical result** (e.g., Negative, Trace, +, ++).
3. Compare interpreted value against normal/expected limits.
4. Mark status flags:
   - normal
   - out-of-range
   - requires review

## 5) Report Generation (PDF)

1. Send interpreted test data to the PDF/report service.
2. Produce report with:
   - company/lab branding
   - standard report structure
   - patient/sample details
   - test-wise results and reference ranges
   - quality notes / confidence indicators
3. Store generated PDF path and checksum for auditability.

## 6) End-to-End Data Storage and Traceability

Store **all stage outputs** under the same unique test ID from start to end:

- capture metadata
- original image
- processed image(s)
- CV JSON output
- interpreted values
- final report PDF
- audit logs and timestamps

This enables complete traceability for validation, QA, and compliance.

## 7) Suggested Pipeline Sequence

1. Create test ID
2. Capture image in controlled box
3. Run CV processing
4. Produce pad-wise JSON output
5. Interpret against reference chart and limits
6. Generate branded PDF report
7. Persist all artifacts in database
8. Expose result via API/dashboard

## 8) Minimal Database Entities

- `tests` (test_id, timestamps, status)
- `captures` (test_id, image_uri, camera metadata)
- `cv_results` (test_id, json_payload, model_version)
- `interpretations` (test_id, analyte, value, flag, reference_range)
- `reports` (test_id, pdf_uri, generated_at)
- `audit_logs` (test_id, stage, event, actor, timestamp)

## 9) Quality and Reliability Checks

- Lighting consistency check before processing
- Blur/focus check on captured image
- Strip detection confidence threshold
- Pad segmentation confidence threshold
- Automatic rejection/re-capture rule when quality is low
- Versioning for CV model and reference chart

---

This reflects the complete process requested in the image: controlled image capture, computer vision extraction, JSON-based color/position output, comparison with normal limits, branded PDF generation, and full database traceability using a unique ID.
