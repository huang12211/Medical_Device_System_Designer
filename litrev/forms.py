from django import forms
from .models import SearchSession

# class FilterArticlesForm(forms.ModelForm):
#     class Meta:
#         model = SearchSession
#         fields = ('gemini_api_key', 'focus',)

class AnalyzeArticlesForm(forms.Form):
    # class Meta:
    #     model = SearchSession
    #     fields = ("gemini_api_key", "focus")
    gemini_api_key = forms.CharField(required=False)
    focus = forms.CharField()
    rel_art_xlsx = forms.FileField()
    # rel_art_pdfs_zip = forms.FileField()
