from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect, FileResponse, JsonResponse
from django.urls import reverse
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt # For simplicity, consider CSRF protection in production

import os
import zipfile
import pandas as pd
from datetime import datetime, timedelta
import time

import asyncio
from asgiref.sync import async_to_sync, sync_to_async

from .models import SearchSession, LitRevSummaryEntry
from .forms import AnalyzeArticlesForm
from .file_manipulations import load_input_rel_articles_xlsx, unzip_zip_files, get_all_file_paths
from .llm_functions import initialize_check_rate, check_rate, initialize_llm, populate_literature_review_summary_dataframe

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
        if "submit" in request.POST:
            form = AnalyzeArticlesForm(request.POST, request.FILES)
            
            if form.is_valid():
                new_analyze_session = SearchSession(filtered_search_xlsx=request.FILES["rel_art_xlsx"],
                                                    filtered_pdfs_zip = request.FILES["rel_art_pdfs_zip"])
                new_analyze_session.gemini_api_key = form.cleaned_data["gemini_api_key"]
                new_analyze_session.focus = form.cleaned_data["focus"]
                new_analyze_session.finished_analyzing = False
                new_analyze_session.save()

                #Processing the data should occur here; Move the logic here;
                # While the data is being processed, the processing wheel will appear. (what if the process is interrrupted mid-process?)
                return HttpResponseRedirect(f"/litrev/analyze-articles/{new_analyze_session.pk}/")
            
        elif "new_session" in request.POST:
            return render(request, 'litrev_pg/analyze_articles.html')

    else:
        return render(request, 'litrev_pg/analyze_articles.html')


def processing_analyze_session(request, analyze_session_id):
    # GET requests should not update the state of the website in any way (the standard is for it to be a read-only feature)
    if request.method == "GET":
        #Display the Input information that led to the results that are available for download.
        #   If the process is not completed for the session, then redirect to a post request to relaunch the processing. 
        #   If processing is completed, then display the download button. 
        s = get_object_or_404(SearchSession, pk=analyze_session_id)
        context = {"session_id": analyze_session_id, 
                   "session_api_key": s.gemini_api_key,
                   "session_focus": s.focus,
                   "session_rel_art_xlsx": s.filtered_search_xlsx,
                   "session_rel_art_pdfs": s.filtered_pdfs_zip,
                   "session_error": 'None',
                   "session_processing_state": ""}
        
        if s.finished_analyzing == False:
            context['session_processing_state'] = "processing"
        else:
            context['session_processing_state'] = 'completed'

        return render(request, 'litrev_pg/analyze_articles_proc.html', context)
    
    elif request.method == "POST":
        if 'submit' in request.POST:
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
            
        elif 'download' in request.POST:
            output_file = './outputs/lit_rev_summary_' + str(analyze_session_id) + '.xlsx'
            try:
                # return FileResponse(output_file.file.open(), as_attachment=True)
                with open(output_file, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(output_file)
                    return response
            except Exception as e:
                print(f"Unable to download file because error: {e}")
                raise Http404
        
        elif 'new_session' in request.POST:
            return HttpResponseRedirect(reverse('litrev:create_analyze_articles'))


###################################################################
# TODO Add logic for urls that don't generate a new html template #
###################################################################
@csrf_exempt # For simplicity, consider CSRF protection in production
async def launch_lit_rev_summary_generation(request, analyze_session_id):
    """Handles the AJAX POST request."""
    if request.method == 'POST':
        # Process the data from request.POST or request.body (for JSON)
        s = await sync_to_async(get_object_or_404)(SearchSession, pk=analyze_session_id)

        # Perform desired actions (e.g., save to database)
        if s.finished_analyzing == False:
            # Load in the xlsx
            pubmed_df = load_input_rel_articles_xlsx("." + str(s.filtered_search_xlsx.url))

            #Read in all of the pdfs listed in the xlsx that are stored in a folder:
            zip_file_path = "." + str(s.filtered_pdfs_zip.url)
            pdfs_extract_directory = "./extracted_pdfs/" + str(s.pk) + "/"
            unzip_zip_files(zip_file_path, pdfs_extract_directory)
            all_pdfs = get_all_file_paths(pdfs_extract_directory)

            #Check Rate to ensure we are not exceeding our rate limits
            initialize_check_rate()

            # Initialize Gemini = Chosen LLM 
            initialize_llm(s.gemini_api_key)

            #Create the Lit Rev Summary DF
            output_file = './outputs/lit_rev_summary_' + str(analyze_session_id) + '.xlsx'
            lit_rev_df, error_message = await populate_literature_review_summary_dataframe(pubmed_df, all_pdfs, s.focus)
            if error_message == None:
                lit_rev_df.to_excel(output_file)
                s.finished_analyzing = True
                try:
                    await sync_to_async(s.save)()
                except Exception as e:
                    error_message = str(e)
                    return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                if "'quotaValue': '10'" in error_message:
                    error_message = "You've exceeded the use of Gemini 2.5 Flash quota per minute, check your rate limiter function"
                elif "'quotaValue': '250'" in error_message:
                    error_message = "You've exceeded the use of Gemini 2.5 Flash quota for the day."
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
        
        return JsonResponse({'status': 'success', 'message': 'Literature Review Summary Generation has been completed'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    