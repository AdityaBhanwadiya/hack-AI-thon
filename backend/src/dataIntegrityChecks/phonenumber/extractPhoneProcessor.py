import json
from uuid import uuid4
import os
import re
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# # Initialize Azure Blob Service Client
# blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
# EXTRACTED_PHONE_CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_PHONE

def extract_phone_from_file(file_path):
    phone_data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            phone_data = extract_phone_numbers(data)
            print(phone_data)
        
        # Generate a unique filename for the extracted phone data
        phone_output_filename = f"extracted_phone_{uuid4()}.json"
        
        # # Save extracted phone data to Azure Blob Storage
        # save_json_to_blob(phone_output_filename, phone_data)
        # print(f"Extracted phone numbers saved to {phone_output_filename} in Azure Blob Storage")

        # Create a list of only phone number values
        phone_values_set = create_phone_set(phone_data)
        print("List of extracted phone numbers:", phone_values_set)

        return phone_values_set
    
    except Exception as e:
        print(f"Error extracting phone numbers: {e}")

# def save_json_to_blob(blob_name, data):
#     """Save JSON content to an Azure Blob."""
#     try:
#         blob_client = blob_service_client.get_blob_client(container=EXTRACTED_PHONE_CONTAINER_NAME, blob=blob_name)
#         blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True)
#         print(f"Successfully saved {blob_name} to Azure Blob Storage.")
#     except Exception as e:
#         print(f"Error saving blob {blob_name}: {e}")

def extract_phone_numbers(data):
    phone_data = {}
    phone_patterns = [
        r'\b\d{10}\b',  # Matches 10-digit phone numbers
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Matches phone numbers in the format 123-456-7890 or 123.456.7890 or 123 456 7890
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'  # Matches phone numbers in the format (123) 456-7890
    ]
    # Compile the patterns to use them in the loop
    phone_regexes = [re.compile(pattern) for pattern in phone_patterns]

    for key, value in data.items():
        if isinstance(value, dict):
            phone_data.update(extract_phone_numbers(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    phone_data.update(extract_phone_numbers(item))
        else:
            for regex in phone_regexes:
                if regex.search(str(value)):
                    phone_data[key] = value
                    break
    return phone_data

def create_phone_set(phone_data):
    phone_values = set(phone_data.values())
    return phone_values