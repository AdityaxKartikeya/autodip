from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DipTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("image", models.ImageField(upload_to="uploads/")),
                ("status", models.CharField(default="uploaded", max_length=32)),
                ("result_json", models.JSONField(blank=True, null=True)),
                ("report_file", models.FileField(blank=True, null=True, upload_to="reports/")),
            ],
        )
    ]
