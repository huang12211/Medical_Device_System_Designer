from django.urls import path
from . import views

#These are your urls to the requested webpages of your app
urlpatterns = [
    #ex:../litrev/
    path("", views.index, name="index"),

    #ex: ../litrev/10/
    path("<int:session_id>/", views.session_id, name="session"),

    #ex: ../litrev/10/filter-articles/
    path("<int:session_id>/filter-articles/", views.filter_articles, name="filter_articles"),

    #ex: ../litrev/10/analyze-articles/
    path("<int:session_id>/analyze-articles/", views.analyze_articles, name = "analyze_articles"),
]