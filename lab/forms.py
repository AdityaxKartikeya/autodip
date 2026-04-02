from django import forms


class UploadDipTestForm(forms.Form):
    image = forms.ImageField(help_text="Upload top-view dip strip image")
