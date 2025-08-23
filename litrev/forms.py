from django import forms
from .models import SearchSession

class FilterArticlesForm(forms.ModelForm):
    class Meta:
        model = SearchSession
        fields = ('session_numb', 'focus',)