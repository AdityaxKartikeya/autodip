from django import forms


class UploadDipTestForm(forms.Form):
    image = forms.ImageField(
        help_text="Upload or drop a top-view dip strip image (PNG/JPEG).",
        widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg", "id": "id_image_input"}),
    )
