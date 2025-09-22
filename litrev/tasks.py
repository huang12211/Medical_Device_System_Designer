from celery import shared_task
# from celery.contrib import rdb
import pandas as pd 
from io import StringIO

from .llm_functions import initialize_check_rate, initialize_llm, populate_literature_review_summary_dataframe, test_celery_task

#Note: all print will be to the terminal for the celery worker aka the terminal where your ran: "celery -A meddevmate worker"

@shared_task
def test_celery():
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'London', 'Paris']
    }
    data = pd.DataFrame(data)
    litrev, error = test_celery_task(data)
    print("litrev", litrev)
    print("error", error)
    litrev_json = litrev.to_json(orient='records')
    return litrev_json, error

@shared_task
def celery_populate_literature_review_summary_dataframe(gemini_api_key, pubmed_df_json, all_pdfs, focus):
    pubmed_df = pd.read_json(StringIO(pubmed_df_json))
    print("all_pdfs", all_pdfs)

    #Check Rate to ensure we are not exceeding our rate limits
    initialize_check_rate()

    # Initialize Gemini = Chosen LLM 
    initialize_llm(gemini_api_key)
    litrev, error = populate_literature_review_summary_dataframe(pubmed_df, all_pdfs, focus)
    litrev_json = litrev.to_json(orient='records')
    return litrev_json, error 