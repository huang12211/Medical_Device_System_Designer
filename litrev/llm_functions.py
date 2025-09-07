from django.shortcuts import get_object_or_404

import os
from datetime import datetime, timedelta
import time
import pandas as pd

from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types
import pathlib
import json

import asyncio
from asgiref.sync import async_to_sync, sync_to_async

from .models import SearchSession
from .file_manipulations import load_input_rel_articles_xlsx, unzip_zip_files, get_all_file_paths

llm_model = "gemini-2.5-flash" #preferred
# llm_model = "gemini-2.5-flash-lite"
rate_per_minute = 10

def initialize_check_rate():
    global numb_calls_this_min
    global first_call_time
    orignal_time = datetime.now()
    numb_calls_this_min = 0
    first_call_time = datetime.now()

def check_rate():
    global numb_calls_this_min
    global first_call_time
    # if numb_calls_this_min == 0:
    #     first_call_time = datetime.now()

    last_call_time = datetime.now()
    time_diff = last_call_time - first_call_time
    # print(f"number_call_this_min: {numb_calls_this_min}; time_diff: {time_diff}")
    if time_diff.total_seconds() < 60: # if we are still within a minute, then we will check if we need to wait before calling the LLM again
        if numb_calls_this_min == rate_per_minute - 1: #if we have reached the max Rate Per Minute, we must figure out how long to wait before calling the LLM again
            wait_time = timedelta(minutes=1) - time_diff
            time.sleep(wait_time.total_seconds() + 5)
            numb_calls_this_min = 1
            first_call_time = datetime.now()
        else:
            numb_calls_this_min = numb_calls_this_min + 1
    else: #a minute has already passed, so we can call the LLM without issue
        numb_calls_this_min = 1
        first_call_time = datetime.now()


####################################################################################
# LLM Content                                                                      #
####################################################################################
def initialize_llm(usr_provided_gemini_api_key):
    global client
    if usr_provided_gemini_api_key != "":
        GOOGLE_API_KEY = usr_provided_gemini_api_key
    else:
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

    client = genai.Client(api_key=GOOGLE_API_KEY)

    #check API Key Validity before proceeding
    test_question = "reply with hello"
    try:
        check_rate()
        test = client.models.generate_content(
                model=llm_model,
                contents=[
                    test_question
                ],
            )
    except:
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
        client = genai.Client(api_key=GOOGLE_API_KEY)

class Technology_Manuf(BaseModel):
    """
    Represents all technology and associated manufacturers listed in the article
    """
    technology: str
    manufacturer: str

class Technology_Manuf_Combo(BaseModel):
    """ 
    Represents a List of paired technology and manufaturers
    """
    tech_manuf: List[Technology_Manuf]

class Sample_Size_Reasoning(BaseModel):
    """ 
    Counts the number of robotically-assisted vs. conventional cases that were examined in the article
    Also provides reasoning that the LLM used to come to these conclusions.
    """
    conv_sample_size: int
    robotic_sample_size: int
    reasoning: str
   
class Harm_Details(BaseModel):
    """
    Represents a single harm and its occurrence count.
    """
    harm_name: str
    occurrence_count: int

class Harms_Count_Confidence(BaseModel):
    """
    Represents all harms-occurences for the article
    """
    harms: List[Harm_Details]
    confidence_score: int

system_ins=["You're a meticulous researcher.",
            "Your mission is to analyze the provided documents and provide accurate answers to requests.",
            "If you do not know the answer to the question, say that you do not know.",
            "Remove all special font formatting from your answer."]

system_ins_harms=["Your mission is to analyze the provided documents and provide accurate answers to requests.",
                  "If you do not know the answer to the question, say that you do not know.",
                  "Provide a confidence score as a percentage to indicate how accurate your answer is to the request."]

async def populate_literature_review_summary_dataframe(pubmed_df, all_pdfs, focus):
    error = None
    lit_rev_df = pd.DataFrame(columns=["Title", "Authors", "Year", "Technology Used", "Manufacturer", 
                                       "Study Type", "Objectives", "Conclusions", "Sample Size", "LLM's Reasoning on Sample Size",
                                       "Harms", "LLM's Confidence in Accuracy of Returned Harms"])

    for i in range(len(pubmed_df)):
        print(f"processing {i+1}th entry of {len(pubmed_df)} of the lit_rev_summary table...")
        ############################################
        # Create the Annex A Table for the Article #
        ############################################
        # read Title from csv
        title = pubmed_df.loc[i, "Title"]

        # read Author from csv
        authors = pubmed_df.loc[i, "Authors"]

        # read Year from csv
        year = pubmed_df.loc[i, "Publication Year"]

        # Retrieve and encode the PDF byte
        first_author = authors.split(",")[0]

        #find the path to the corresponding pdf 
        for j in range(len(all_pdfs)):
            if first_author in all_pdfs[j] and str(year) in all_pdfs[j]:
                filepath = pathlib.Path(all_pdfs[j])

        # Manufacturer & Tech from LLM 
        print("finding manufacturer")
        question = "Identify the manufacturers of the technologies listed"
        check_rate()
        try:
            manufacturer_tech = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(data=filepath.read_bytes(), mime_type='application/pdf'),
                    question
                ],
                config = types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=Technology_Manuf_Combo.model_json_schema(),
                    system_instruction = system_ins
                )
            )
        except Exception as e:
            error = str(e)
            break
            
        final_manuf_tech = json.loads(manufacturer_tech.text)
        tech_text = ""
        manufacturer_text = ""
        for k in range(len(final_manuf_tech["tech_manuf"])):
            tech_text = tech_text + str(k+1) + ". " + final_manuf_tech["tech_manuf"][k]["technology"] + "\n"
            manufacturer_text = manufacturer_text + str(k+1) + ". " + final_manuf_tech["tech_manuf"][k]["manufacturer"] + "\n"


        # Study Type from LLM (check if you can export this directly from Pubmed somehow.....)
        print("finding study type")
        question = "Identify the type of study that was performed by the article. If the study type is unclear, return 'Study Type Unknown'."
        check_rate()
        try:
            study_type = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(), 
                        mime_type='application/pdf'
                    ),
                    question
                ],
                config = types.GenerateContentConfig(
                    system_instruction = system_ins
                )
            )
        except Exception as e:
            error = str(e)
            break

        # Objective of the Article from LLM
        print("finding objective")
        question = "Provide a brief summary of the objective(s) of the article"
        check_rate()
        try:
            objective = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    question
                ],
                config = types.GenerateContentConfig(
                    system_instruction = system_ins
                )
            )
        except Exception as e:
            error = str(e)
            break

        # Conclusion from LLM 
        print("finding conclusion")
        question = "Provide a brief summary of the conclusion(s) of the article"
        check_rate()
        try:
            conclusion = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    question
                ],
                config = types.GenerateContentConfig(
                    system_instruction = system_ins
                )
            )
        except Exception as e:
            error = str(e)
            break

        # Patient Sample size from LLM
        print("finding sample size")
        question = f"Find the number of adult patients that underwent conventional surgery compared to {focus}"
        check_rate()
        try:
            sample_size = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    question
                ],
                config = types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=Sample_Size_Reasoning.model_json_schema(),
                    system_instruction = system_ins
                )
            )
        except Exception as e:
            error = str(e)
            break
        final_sample = json.loads(sample_size.text)
        sample_size_text = f"conventional: {str(final_sample['conv_sample_size'])} \n" + f"{focus}: {str(final_sample["robotic_sample_size"])} \n" 
        sample_reasoning_text = final_sample["reasoning"]
        

        # Hazards and Harms from LLM 
        print("finding hazards and harms")
        step_by_step_prompt = f"""
        Let's go through this step by step. 
        First, list the number of observed hazards, harms, adverse events, and complications. 
        Second, remove any that occurred due to elements unrelated to the {focus}. 
        Third, if no more entries exist, then return ['No specific hazards, harms, adverse events, or complications were reported', 0]. Otherwise, count the number of occurrence of each entry. 
        """
        check_rate()
        try:
            harms = client.models.generate_content(
                model=llm_model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    step_by_step_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=Harms_Count_Confidence.model_json_schema(),
                    system_instruction = system_ins_harms
                ),
            )
        except Exception as e:
            error = str(e)
            break
        
        final_harms = json.loads(harms.text)
        harm_text = ""
        for k in range(len(final_harms["harms"])):
            if "No specific hazards" not in final_harms["harms"][k]["harm_name"]:
                harm_text = harm_text + final_harms["harms"][k]["harm_name"] + ": " + str(final_harms["harms"][k]["occurrence_count"]) + "\n"

        if len(harm_text) == 0:
            harm_text = "No specific hazards, adverse events, or complications were reported"
            
        harms_conf_score = "The LLM is " + str(final_harms["confidence_score"]) + f"% sure of its answer."

        row = pd.DataFrame(data = {"Title": title, 
                                    "Authors": authors, 
                                    "Year": year, 
                                    "Technology Used": tech_text, 
                                    "Manufacturer": manufacturer_text, 
                                    "Study Type": study_type.text, 
                                    "Objectives": objective.text, 
                                    "Conclusions": conclusion.text, 
                                    "Sample Size": sample_size_text, 
                                    "LLM's Reasoning on Sample Size": sample_reasoning_text,
                                    "Harms": harm_text,
                                    "LLM's Confidence in Accuracy of Returned Harms": harms_conf_score
                                    },
                            index = [i])

        lit_rev_df = pd.concat([lit_rev_df, row], ignore_index=True)

    return lit_rev_df, error

# async def populate_literature_review_summary_dataframe(analyze_session_id, output_file, context):
#     s = await sync_to_async(get_object_or_404)(SearchSession, pk=analyze_session_id)
#     focus = s.focus

#     # Load in the xlsx
#     pubmed_df = load_input_rel_articles_xlsx("." + str(s.filtered_search_xlsx.url))

#     #Read in all of the pdfs listed in the xlsx that are stored in a folder:
#     zip_file_path = "." + str(s.filtered_pdfs_zip.url)
#     pdfs_extract_directory = "./extracted_pdfs/" + str(s.pk) + "/"
#     unzip_zip_files(zip_file_path, pdfs_extract_directory)
#     all_pdfs = get_all_file_paths(pdfs_extract_directory)

#     #Check Rate to ensure we are not exceeding our rate limits
#     initialize_check_rate()

#     # Initialize Gemini = Chosen LLM 
#     initialize_llm(s.gemini_api_key)

#     error = None
#     lit_rev_df = pd.DataFrame(columns=["Title", "Authors", "Year", "Technology Used", "Manufacturer", 
#                                        "Study Type", "Objectives", "Conclusions", "Sample Size", "LLM's Reasoning on Sample Size",
#                                        "Harms", "LLM's Confidence in Accuracy of Returned Harms"])

#     for i in range(len(pubmed_df)):
#         print(f"processing {i+1}th entry of {len(pubmed_df)} of the lit_rev_summary table...")
#         ############################################
#         # Create the Annex A Table for the Article #
#         ############################################
#         # read Title from csv
#         title = pubmed_df.loc[i, "Title"]

#         # read Author from csv
#         authors = pubmed_df.loc[i, "Authors"]

#         # read Year from csv
#         year = pubmed_df.loc[i, "Publication Year"]

#         # Retrieve and encode the PDF byte
#         first_author = authors.split(",")[0]

#         #find the path to the corresponding pdf 
#         for j in range(len(all_pdfs)):
#             if first_author in all_pdfs[j] and str(year) in all_pdfs[j]:
#                 filepath = pathlib.Path(all_pdfs[j])

#         # Manufacturer & Tech from LLM 
#         print("finding manufacturer")
#         question = "Identify the manufacturers of the technologies listed"
#         check_rate()
#         try:
#             manufacturer_tech = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(data=filepath.read_bytes(), mime_type='application/pdf'),
#                     question
#                 ],
#                 config = types.GenerateContentConfig(
#                     response_mime_type='application/json',
#                     response_schema=Technology_Manuf_Combo.model_json_schema(),
#                     system_instruction = system_ins
#                 )
#             )
#         except Exception as e:
#             error = str(e)
#             break
            
#         final_manuf_tech = json.loads(manufacturer_tech.text)
#         tech_text = ""
#         manufacturer_text = ""
#         for k in range(len(final_manuf_tech["tech_manuf"])):
#             tech_text = tech_text + str(k+1) + ". " + final_manuf_tech["tech_manuf"][k]["technology"] + "\n"
#             manufacturer_text = manufacturer_text + str(k+1) + ". " + final_manuf_tech["tech_manuf"][k]["manufacturer"] + "\n"


#         # Study Type from LLM (check if you can export this directly from Pubmed somehow.....)
#         print("finding study type")
#         question = "Identify the type of study that was performed by the article. If the study type is unclear, return 'Study Type Unknown'."
#         check_rate()
#         try:
#             study_type = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(
#                         data=filepath.read_bytes(), 
#                         mime_type='application/pdf'
#                     ),
#                     question
#                 ],
#                 config = types.GenerateContentConfig(
#                     system_instruction = system_ins
#                 )
#             )
#         except Exception as e:
#             error = str(e)
#             break

#         # Objective of the Article from LLM
#         print("finding objective")
#         question = "Provide a brief summary of the objective(s) of the article"
#         check_rate()
#         try:
#             objective = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(
#                         data=filepath.read_bytes(),
#                         mime_type='application/pdf',
#                     ),
#                     question
#                 ],
#                 config = types.GenerateContentConfig(
#                     system_instruction = system_ins
#                 )
#             )
#         except Exception as e:
#             error = str(e)
#             break

#         # Conclusion from LLM 
#         print("finding conclusion")
#         question = "Provide a brief summary of the conclusion(s) of the article"
#         check_rate()
#         try:
#             conclusion = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(
#                         data=filepath.read_bytes(),
#                         mime_type='application/pdf',
#                     ),
#                     question
#                 ],
#                 config = types.GenerateContentConfig(
#                     system_instruction = system_ins
#                 )
#             )
#         except Exception as e:
#             error = str(e)
#             break

#         # Patient Sample size from LLM
#         print("finding sample size")
#         question = f"Find the number of adult patients that underwent conventional surgery compared to {focus}"
#         check_rate()
#         try:
#             sample_size = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(
#                         data=filepath.read_bytes(),
#                         mime_type='application/pdf',
#                     ),
#                     question
#                 ],
#                 config = types.GenerateContentConfig(
#                     response_mime_type='application/json',
#                     response_schema=Sample_Size_Reasoning.model_json_schema(),
#                     system_instruction = system_ins
#                 )
#             )
#         except Exception as e:
#             error = str(e)
#             break
#         final_sample = json.loads(sample_size.text)
#         sample_size_text = f"conventional: {str(final_sample['conv_sample_size'])} \n" + f"{focus}: {str(final_sample["robotic_sample_size"])} \n" 
#         sample_reasoning_text = final_sample["reasoning"]
        

#         # Hazards and Harms from LLM 
#         print("finding hazards and harms")
#         step_by_step_prompt = f"""
#         Let's go through this step by step. 
#         First, list the number of observed hazards, harms, adverse events, and complications. 
#         Second, remove any that occurred due to elements unrelated to the {focus}. 
#         Third, if no more entries exist, then return ['No specific hazards, harms, adverse events, or complications were reported', 0]. Otherwise, count the number of occurrence of each entry. 
#         """
#         check_rate()
#         try:
#             harms = client.models.generate_content(
#                 model=llm_model,
#                 contents=[
#                     types.Part.from_bytes(
#                         data=filepath.read_bytes(),
#                         mime_type='application/pdf',
#                     ),
#                     step_by_step_prompt
#                 ],
#                 config=types.GenerateContentConfig(
#                     response_mime_type='application/json',
#                     response_schema=Harms_Count_Confidence.model_json_schema(),
#                     system_instruction = system_ins_harms
#                 ),
#             )
#         except Exception as e:
#             error = str(e)
#             break
        
#         final_harms = json.loads(harms.text)
#         harm_text = ""
#         for k in range(len(final_harms["harms"])):
#             if "No specific hazards" not in final_harms["harms"][k]["harm_name"]:
#                 harm_text = harm_text + final_harms["harms"][k]["harm_name"] + ": " + str(final_harms["harms"][k]["occurrence_count"]) + "\n"

#         if len(harm_text) == 0:
#             harm_text = "No specific hazards, adverse events, or complications were reported"
            
#         harms_conf_score = "The LLM is " + str(final_harms["confidence_score"]) + f"% sure of its answer."

#         row = pd.DataFrame(data = {"Title": title, 
#                                     "Authors": authors, 
#                                     "Year": year, 
#                                     "Technology Used": tech_text, 
#                                     "Manufacturer": manufacturer_text, 
#                                     "Study Type": study_type.text, 
#                                     "Objectives": objective.text, 
#                                     "Conclusions": conclusion.text, 
#                                     "Sample Size": sample_size_text, 
#                                     "LLM's Reasoning on Sample Size": sample_reasoning_text,
#                                     "Harms": harm_text,
#                                     "LLM's Confidence in Accuracy of Returned Harms": harms_conf_score
#                                     },
#                             index = [i])

#         lit_rev_df = pd.concat([lit_rev_df, row], ignore_index=True)
    
#     if error == None:
#         lit_rev_df.to_excel(output_file)
#         context['session_error'] = 'None'
#         context['session_processing_state'] = 'completed'
#         s.finished_analyzing = True
#         s.save()
#     else:
#         if "'quotaValue': '10'" in error:
#             error = "You've exceeded the use of Gemini 2.5 Flash quota per minute, check your rate limiter function"
#         elif "'quotaValue': '250'" in error:
#             error = "You've exceeded the use of Gemini 2.5 Flash quota for the day."
#         context["session_error"] = f"Error Occurred: {error}"

#     return context