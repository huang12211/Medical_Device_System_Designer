from django.db import models

# Create your models here.
class SearchSession(models.Model):
    session_numb = models.IntegerField()
    focus = models.CharField(max_length=250)
    # search_input_csv = #TO DO# 
    # filtered_search_csv = # TO DO#
    # missing_pdfs_xlsx = # To Do
    def __int__(self):
        return self.session_numb


class SearchResults(models.Model):
    session_numb = models.ForeignKey(SearchSession, on_delete=models.CASCADE)
    pdf_filename = models.CharField()
    # pdf_content_ = #TO DO: BYTEA# 
    def __str__(self):
        return self.pdf_filename
