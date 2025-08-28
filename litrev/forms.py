from django import forms
from .models import SearchSession

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class AnalyzeArticlesForm(forms.Form):
    gemini_api_key = forms.CharField(required=False)
    focus = forms.CharField()
    rel_art_xlsx = forms.FileField()
    rel_art_pdfs_zip = MultipleFileField()
