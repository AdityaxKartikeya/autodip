from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from lab.forms import UploadDipTestForm
from lab.models import DipTest
from lab.services import process_dip_test


def dashboard(request):
    if request.method == "POST":
        form = UploadDipTestForm(request.POST, request.FILES)
        if form.is_valid():
            test = DipTest.objects.create(image=form.cleaned_data["image"], status="processing")
            process_dip_test(test)
            messages.success(request, f"Dip test #{test.id} processed successfully.")
            return redirect("diptest_detail", test_id=test.id)
    else:
        form = UploadDipTestForm()

    tests = DipTest.objects.order_by("-created_at")[:20]
    return render(request, "lab/dashboard.html", {"form": form, "tests": tests})


def diptest_detail(request, test_id: int):
    test = get_object_or_404(DipTest, id=test_id)
    return render(request, "lab/detail.html", {"test": test})
