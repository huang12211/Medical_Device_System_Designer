from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from .models import SearchSession

# Create your views here. These return either: just data, or data rendered in a webpage; 

def index(request): # Where you create a new session???
    return render(request, 'litrev_pg/index.html')

def session_id(request, session_id): #not a useful view; delete. 
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, "litrev_pg/session.html", context)

def filter_articles(request, session_id):
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, 'litrev_pg/filter_articles.html', context)

def analyze_articles(request, session_id):
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, 'litrev_pg/analyze_articles.html', context)
