from django.urls import path
from . import views

#These are your urls to the requested webpages of your app
app_name = "litrev"
urlpatterns = [
    #ex:../litrev/
    path("", views.index, name="index"),


    #ex: ../litrev/10/populate-incl-excl-criteria/
    #Update the Inclusion/Exclusion criteria for papers
    # path("<int:session_id>/populate-incl-excl-criteria/", views.create_session, name="create_session"),

    #ex: ../litrev/10/filtered-articles/
    # Displays the inputs and results of the filtering of the original list based on content in the abstracts for that session
    path("<int:session_id>/filter-articles/", views.filter_articles, name="filter_articles"),

    #ex: ../litrev/analyze-articles/
    # Contains an empty form to accept following input data which when submitted, creates a new search session in the database:
    #   - Optional: A fresh Google Gemini's API Key
    #   - Focus Theme/Subject/Technology of the literature review
    #   - Excel file of shortlisted relevant articles
    #   - Zip file of All PDFs of Relevant Articles
    path("analyze-articles/", views.create_analyze_session, name = "create_analyze_articles"),

    #ex: ../litrev/analyze-articles/processing/10
    # Displays the input data that was submitted for the session and allows them to download the associated results
    # Allows the user to modify the data that was submitted for the session
    path("analyze-articles/processing/<int:analyze_session_id>/", views.processing_analyze_session, name="processing_analyze_session"),

    #ex: ../litrev/analyze-articles/10/
    # path("analyze-articles/<int:analyze_session_id>/", views.analyze_session_info, name = "analyze_session_info"),
]