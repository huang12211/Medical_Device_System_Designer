from django.contrib import admin
from .models import SearchSession, SearchResults

# Register your models here.
admin.site.register(SearchSession)
admin.site.register(SearchResults)
