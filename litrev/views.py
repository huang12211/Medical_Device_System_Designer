from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from .models import SearchSession
from .forms import FilterArticlesForm

# Create your views here. These return either: just data, or data rendered in a webpage; 

def index(request): # Where you create a new session???
    return render(request, 'litrev_pg/index.html')

def session_id(request, session_id): #get information for session
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, "litrev_pg/session.html", context)

def create_session(request):
    if request.method == "POST": #When the method is "POST", it means that the form was submitted 
        form = FilterArticlesForm(request.POST)
        if form.is_valid():
            form = form.save()
    else:
        form = FilterArticlesForm()
        return render(request, 'litrev_pg/filter_articles.html', {"form":form})

def filter_articles(request, session_id):
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, 'litrev_pg/filter_articles.html', context)

def analyze_articles(request, session_id):
    session_num = get_object_or_404(SearchSession, pk = session_id)
    context = {"session": session_num}
    return render(request, 'litrev_pg/analyze_articles.html', context)
