from django.contrib import admin
from .models import SearchSession, LitRevSummaryEntry, SearchSessionPDFs

# Register your models here.
admin.site.register(SearchSession)
admin.site.register(LitRevSummaryEntry)
admin.site.register(SearchSessionPDFs)
