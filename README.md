# AutoDip (Django Dashboard + Admin)

AutoDip now includes a Django web dashboard where users can upload a urine dip-strip image and run the full processing pipeline.

## Features

- Dashboard upload page (`/`) to submit dip-strip images.
- End-to-end pipeline on upload:
  1. CV extraction from image (`autodip/cv.py`)
  2. Clinical interpretation (`autodip/workflow.py`)
  3. Report generation (`autodip/report.py`)
  4. Data persistence in Django DB (`lab.models.DipTest`)
- Django admin panel (`/admin/`) for operational review.
- First dashboard request auto-runs migrations if DB tables are missing (still recommended to run migrate manually).

## Setup

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Dashboard: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Notes

- Current CV extractor is an initial heuristic (center-strip segmentation into 10 pads).
- Interpretation now maps pad RGB to analyte-specific reference color charts (including pH and specific gravity scales).
- Report generation now emits a real downloadable PDF file (without third-party PDF deps).
- Dashboard upload has a drag-and-drop dropzone for faster workflow.


## ML Classifier (scikit-learn)

A simple per-analyte ML classifier is available in `autodip/ml_classifier.py`.

Features used per sample:
- RGB: `R, G, B`
- HSV: `H, S, V`
- Ratios: `R/G, R/B, G/B`
- Brightness

Training sample format (`sample_training_data.json`):

```json
[
  {"analyte": "glucose", "rgb": [245, 222, 179], "label": "negative"},
  {"analyte": "glucose", "rgb": [220, 170, 60], "label": "slightly_high"}
]
```

Run:

```bash
python -m autodip.ml_classifier sample_training_data.json random_forest
```

This prints per-analyte accuracy and confusion matrix, and an example prediction with confidence.
