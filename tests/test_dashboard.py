import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from PIL import Image

from lab.models import DipTest


def make_test_image() -> bytes:
    img = Image.new("RGB", (300, 1000), color=(180, 160, 120))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


class DashboardFlowTests(TestCase):
    def test_upload_runs_pipeline(self):
        client = Client()
        image = SimpleUploadedFile("strip.png", make_test_image(), content_type="image/png")

        response = client.post("/", {"image": image}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(DipTest.objects.count(), 1)

        record = DipTest.objects.first()
        self.assertEqual(record.status, "completed")
        self.assertIn("output", record.result_json)
        self.assertTrue(bool(record.report_file))
        self.assertTrue(record.report_file.read().startswith(b"%PDF-"))
