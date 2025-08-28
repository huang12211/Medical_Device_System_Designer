from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import FormView

import os
import zipfile
import pandas as pd
from datetime import datetime, timedelta
import time

from .models import SearchSession, LitRevSummaryEntry
from .forms import AnalyzeArticlesForm
from .file_manipulations import load_input_rel_articles_xlsx, get_all_file_paths
from .llm_functions import initialize_check_rate, check_rate, initialize_llm, check_llm_api_key_validity, populate_literature_review_summary_dataframe

#For debuggin
import logging
import pdb

DEBUG = (os.environ.get('DJANGO_ENV', 'production') == 'development')
if DEBUG:
    logger = logging
    logger = logging.getLogger(__name__)

class AnalyzeArticlesFormView(FormView):
    form_class = AnalyzeArticlesForm
    template_name = "upload.html"  # Replace with your template.
    success_url = "..."  # Replace with your URL or reverse().

    def form_valid(self, form):
        files = form.cleaned_data["rel_art_pdfs_zip"]
        for f in files:
            ...  # Do something with each file.
        return super().form_valid(form)

# Create your views here. These return either: just data, or data rendered in a webpage; 
def index(request): # Where you create a new session???
    return render(request, 'litrev_pg/index.html')


def filter_articles(request, session_id):
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, 'litrev_pg/filter_articles.html', context)


def create_analyze_session(request):
    if request.method == "GET":
        return render(request, 'litrev_pg/analyze_articles.html')
    
    elif request.method == "POST": #When the method is "POST", it means that the form was submitted 
        form = AnalyzeArticlesForm(request.POST, request.FILES)
        
        if form.is_valid():
            new_analyze_session = SearchSession(filtered_search_xlsx=request.FILES["rel_art_xlsx"],
                                                filtered_pdfs_zip = request.FILES["rel_art_pdfs_zip"])
            new_analyze_session.gemini_api_key = form.cleaned_data["gemini_api_key"]
            new_analyze_session.focus = form.cleaned_data["focus"]
            new_analyze_session.save()
            return HttpResponseRedirect(f"/litrev/analyze-articles/processing/{new_analyze_session.pk}/")

    else:
        return render(request, 'litrev_pg/analyze_articles.html')


def processing_analyze_session(request, analyze_session_id):
    if request.method == "GET":
        #Display the Input information that led to the results that are available for download.
        s = get_object_or_404(SearchSession, pk = analyze_session_id)
        context = {"session_api_key": s.gemini_api_key,
                   "session_focus": s.focus,
                   "session_rel_art_xlsx": s.filtered_search_xlsx,
                   "session_rel_art_pdfs": s.filtered_pdfs_zip}

        ############################################################################
        # Logic for Launching the LLMs to process the data that has been inputted. #
        ############################################################################
        # Load in the xlsx
        pubmed_df = load_input_rel_articles_xlsx("." + str(s.filtered_search_xlsx.url))

        #Read in all of the pdfs listed in the xlsx that are stored in a folder:

        zip_file_path = "." + str(s.filtered_pdfs_zip.url)
        pdfs_extract_directory = "./extracted_pdfs/" + str(s.pk) + "/"
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(pdfs_extract_directory)
            print(f"Successfully extracted '{zip_file_path}' to '{pdfs_extract_directory}'")
        except zipfile.BadZipFile:
            print(f"Error: '{zip_file_path}' is not a valid ZIP file or is corrupted.")
        except FileNotFoundError:
            print(f"Error: ZIP file '{zip_file_path}' not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        all_pdfs = get_all_file_paths(pdfs_extract_directory)

        # Initialize Gemini = Chosen LLM 
        initialize_llm(s.gemini_api_key)
        api_key = check_llm_api_key_validity()

        #Check Rate to ensure we are not exceeding our rate limits
        initialize_check_rate()
        check_rate()
        
        #Create the Lit Rev Summary DF
        lit_rev_df = populate_literature_review_summary_dataframe(pubmed_df, all_pdfs, s.focus)

        lit_rev_df.to_excel('./outputs/lit_rev_summary_' + str(s.pk) + '.xlsx')

        return render(request, 'litrev_pg/analyze_articles_proc.html', context)
    
    elif request.method == "POST": #TODO
        form = AnalyzeArticlesForm(request.POST, request.FILES)
        if form.is_valid():
            s = get_object_or_404(SearchSession, pk = analyze_session_id)
            s.gemini_api_key = form.cleaned_data["gemini_api_key"]
            s.focus = form.cleaned_data["focus"]
            s.filtered_search_xlsx = form.cleaned_data["rel_art_xlsx"]
            s.filtered_pdfs_zip = form.cleaned_data["rel_art_pdfs_zip"]
            s.save()
            context = {"session_api_key": s.gemini_api_key,
                       "session_focus": s.focus,
                       "session_rel_art_xlsx": s.filtered_search_xlsx,
                       "session_rel_art_pdfs": s.filtered_pdfs_zip}
            return render(request, 'litrev_pg/analyze_articles_proc.html', context)


        

    


