from django.urls import path

from lab import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tests/<int:test_id>/", views.diptest_detail, name="diptest_detail"),
]
