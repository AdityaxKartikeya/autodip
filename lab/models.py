from django.db import models


class DipTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="uploads/")
    status = models.CharField(max_length=32, default="uploaded")
    result_json = models.JSONField(null=True, blank=True)
    report_file = models.FileField(upload_to="reports/", null=True, blank=True)

    def __str__(self) -> str:
        return f"DipTest #{self.pk} - {self.status}"
