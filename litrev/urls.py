from django.urls import path
from . import views

#These are your urls to the requested webpages of your app
app_name = "litrev"
urlpatterns = [
    #ex:../litrev/
    path("", views.index, name="index"),

    #ex: ../litrev/create/
    # Contains a form to accept following input data which when completed, is fulfilled:
    #   - Pubmed search csv file listing all pdfs
    #   - Focus Theme/Subject/Technology of the literature review
    path("create/", views.create_session, name="create_session"),

    #ex: ../litrev/10/
    # Retrieve all existing data related to the session in progress
    path("<int:session_id>/", views.session_id, name="session"),

    #ex: ../litrev/10/populate-incl-excl-criteria/
    #Update the Inclusion/Exclusion criteria for papers
    # path("<int:session_id>/populate-incl-excl-criteria/", views.create_session, name="create_session"),

    #ex: ../litrev/10/filtered-articles/
    # Displays the inputs and results of the filtering of the original list based on content in the abstracts for that session
    path("<int:session_id>/filter-articles/", views.filter_articles, name="filter_articles"),

    #ex: ../litrev/10/analyze-articles/
    path("<int:session_id>/analyze-articles/", views.analyze_articles, name = "analyze_articles"),
]