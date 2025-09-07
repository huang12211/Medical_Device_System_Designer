import os
import pandas as pd
import zipfile

def load_input_rel_articles_xlsx(path):
    pubmed_df = pd.read_excel(path)
    try:
        pubmed_df = pubmed_df.drop(['Citation', 'First Author', 'Create Date', 'PMCID', 'NIHMS ID'], axis=1)
    except:
        print("not a csv")

    pubmed_df['Title'] = pubmed_df['Title'].astype(str)
    pubmed_df['Authors'] = pubmed_df['Authors'].astype(str)
    return pubmed_df

def unzip_zip_files(input_path, output_path):
    try:
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            zip_ref.extractall(output_path)
        print(f"Successfully extracted '{input_path}' to '{output_path}'")
    except zipfile.BadZipFile:
        print(f"Error: '{input_path}' is not a valid ZIP file or is corrupted.")
    except FileNotFoundError:
        print(f"Error: ZIP file '{input_path}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_all_file_paths(directory_path):
    """
    Collects the absolute paths of all files within a given directory
    and its subdirectories.

    Args:
        directory_path (str): The path to the directory to traverse.

    Returns:
        list: A list containing the absolute paths of all found files.
    """
    file_paths = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            full_path = os.path.join(root, file)
            file_paths.append(os.path.abspath(full_path))
    return file_paths
