from django.db import models

# Create your models here.
class SearchSession(models.Model):
    gemini_api_key = models.CharField(blank=True)
    focus = models.CharField()
    # search_input_csv = #TO DO# 
    filtered_search_xlsx = models.FileField(upload_to="uploads/") #contains the path to the xlsx itself
    filtered_pdfs_zip = models.FileField(upload_to="uploads/") #contains the path to the .zip itself
    # missing_pdfs_xlsx = # To Do
    finished_analyzing = models.BooleanField()
    def __int__(self):
        return self.pk

class LitRevSummaryEntry(models.Model):
    session_numb = models.ForeignKey(SearchSession, on_delete=models.CASCADE)
    title = models.CharField()
    authors = models.CharField()
    year = models.PositiveIntegerField()
    technology = models.CharField()
    manufacturer = models.CharField()
    study_type = models.CharField()
    objective = models.CharField()
    conclusion = models.CharField()
    sample_size = models.CharField()
    LLM_reasoning_sample_size = models.CharField()
    hazards_harms = models.CharField()
    LLM_confidence_hazards_harms = models.CharField()


class SearchSessionPDFs(models.Model):
    #before we have multiple sessions running simultaneously, we will keep the session_numb relationship as "Many to One"; Later, it can be altered to become a "Many to Many" relationship instead
    session_numb = models.ForeignKey(SearchSession, on_delete=models.CASCADE) 
    pdf_filename = models.CharField()
    # pdf_content = #TO DO: BYTEA# 
    def __str__(self):
        return self.pdf_filename
