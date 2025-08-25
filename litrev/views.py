from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from .models import SearchSession, LitRevSummaryEntry
from .forms import AnalyzeArticlesForm
import os
import logging
import pdb

DEBUG = (os.environ.get('DJANGO_ENV', 'production') == 'development')
if DEBUG:
    logger = logging
    logger = logging.getLogger(__name__)

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
            new_analyze_session = SearchSession(filtered_search_xlsx=request.FILES["rel_art_xlsx"])
            # new_analyze_session.gemini_api_key = request.POST["gemini_api_key"]
            # new_analyze_session.focus = request.POST["focus"]
            new_analyze_session.gemini_api_key = form.cleaned_data["gemini_api_key"]
            new_analyze_session.focus = form.cleaned_data["focus"]
            new_analyze_session.save()
            return HttpResponseRedirect(f"/litrev/analyze-articles/processing/{new_analyze_session.pk}/")

    else:
        return render(request, 'litrev_pg/analyze_articles.html')


def processing_analyze_session(request, analyze_session_id):
    if request.method == "GET":
        s = get_object_or_404(SearchSession, pk = analyze_session_id)
        context = {"session_api_key": s.gemini_api_key,
                   "session_focus": s.focus,
                   "session_rel_art_xlsx": s.filtered_search_xlsx}
        return render(request, 'litrev_pg/analyze_articles_proc.html', context)
    
    elif request.method == "POST":
        form = AnalyzeArticlesForm(request.POST, request.FILES)
        if form.is_valid():
            s = get_object_or_404(SearchSession, pk = analyze_session_id)
            s.gemini_api_key = form.cleaned_data["gemini_api_key"]
            s.focus = form.cleaned_data["focus"]
            s.filtered_search_xlsx = form.cleaned_data["rel_art_xlsx"]
            s.save()
            context = {"session_api_key": s.gemini_api_key,
                       "session_focus": s.focus,
                       "session_rel_art_xlsx": s.filtered_search_xlsx}
            return render(request, 'litrev_pg/analyze_articles_proc.html', context)
        

    


