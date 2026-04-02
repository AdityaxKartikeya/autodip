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
- Report generation currently writes text content to a `.pdf` filename placeholder for later PDF-engine integration.
