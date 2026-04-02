from __future__ import annotations

from django.contrib import messages
from django.db.utils import OperationalError
from django.shortcuts import get_object_or_404, redirect, render

from lab.bootstrap import ensure_schema
from lab.forms import UploadDipTestForm
from lab.models import DipTest
from lab.services import process_dip_test


def dashboard(request):
    try:
        ensure_schema()
    except Exception as exc:  # keep dashboard responsive if auto-migrate fails
        messages.warning(request, f"Database bootstrap failed: {exc}. Run `python manage.py migrate`.")

    if request.method == "POST":
        form = UploadDipTestForm(request.POST, request.FILES)
        if form.is_valid():
            test = DipTest.objects.create(image=form.cleaned_data["image"], status="processing")
            process_dip_test(test)
            messages.success(request, f"Dip test #{test.id} processed successfully.")
            return redirect("diptest_detail", test_id=test.id)
    else:
        form = UploadDipTestForm()

    try:
        tests = DipTest.objects.order_by("-created_at")[:20]
    except OperationalError:
        tests = []
        messages.warning(request, "Database tables are missing. Please run `python manage.py migrate`.")

    return render(request, "lab/dashboard.html", {"form": form, "tests": tests})


def diptest_detail(request, test_id: int):
    ensure_schema()
    test = get_object_or_404(DipTest, id=test_id)
    return render(request, "lab/detail.html", {"test": test})
