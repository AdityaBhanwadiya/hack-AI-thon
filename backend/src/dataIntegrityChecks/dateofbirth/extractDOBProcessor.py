import json
import re
from uuid import uuid4
import os
import backend.src.dataIntegrityChecks.dateofbirth.checkDOB as checkDOB
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

def extract_dob_from_file(file_path):
    dob_data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            dob_data = extract_dob(data)

        # Create a list of only DOB values
        dob_values_list = create_dob_set(dob_data)
        # Remove empty string and None values from the list
        filtered_dob_values_list = [dob for dob in dob_values_list if dob and dob.strip()]
        print("List of extracted DOB values:", filtered_dob_values_list)

        wrongFormattedDates = checkDOBFormat(filtered_dob_values_list)
        return wrongFormattedDates
    except Exception as e:
        print(f"Error extracting DOBs: {e}")

def extract_dob(data):
    dob_data = {}
    dob_patterns = [
        r'\bdob\b', r'date[_\s]*of[_\s]*birth', r'birth[_\s]*date', r'birth[_\s]*date'
    ]
    # Compile the patterns to use them in the loop
    dob_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in dob_patterns]

    for key, value in data.items():
        if isinstance(value, dict):
            dob_data.update(extract_dob(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    dob_data.update(extract_dob(item))
        else:
            for regex in dob_regexes:
                if regex.search(key):
                    dob_data[key] = value
                    break
    return dob_data

def create_dob_set(dob_data):
    dob_values = set(dob_data.values())
    return dob_values

def checkDOBFormat(dob_data_list):
    wrongFormattedDates = {}

    for dob in dob_data_list:
        if not checkDOB.validate_birthdate(dob):
            wrongFormattedDates[dob] = "False"
    return wrongFormattedDates
