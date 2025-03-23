import json
import re
import os
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
ORGANISED_CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA

def replace_dob_in_blob(organised_output_blob_name, wrongFormattedDOBs):
    # Load the organized output file content from Azure Blob Storage
    content = load_json_from_blob(organised_output_blob_name, ORGANISED_CONTAINER_NAME)
    if content is None:
        print(f"Error: Failed to load organized output from {organised_output_blob_name}.")
        return

    # If wrongFormattedDOBs is empty, exit the function early
    if not wrongFormattedDOBs:
        print("No DOBs to replace. Exiting function.")
        return

    # Replace occurrences of wrongFormattedDOBs with "I CAN'T READ THIS"
    updated_content = json.dumps(content)  # Convert JSON object to a string
    for dob in wrongFormattedDOBs:
        # Use regex to ensure the exact match of DOB (if DOB has a standard format)
        updated_content = re.sub(rf'\b{re.escape(dob)}\b', "I CAN'T READ THIS", updated_content)

    # Convert string back to JSON
    updated_json_content = json.loads(updated_content)

    # Save the updated JSON back to the Azure Blob Storage
    save_json_to_blob(organised_output_blob_name, updated_json_content)
    print(f"DOB: Updated {organised_output_blob_name} with replacements.")

def load_json_from_blob(blob_name, container_name):
    """Load JSON content from an Azure Blob."""
    try:
        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Define the path for the downloaded file
        downloaded_file_path = os.path.join("/tmp", blob_name)
        
        # Download the blob content to a temporary file
        with open(downloaded_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        # Read the downloaded file and parse the JSON content
        with open(downloaded_file_path, "r") as file:
            data = json.load(file)
        
        return data
    except json.JSONDecodeError as je:
        print(f"JSON decode error for blob {blob_name}: {je}")
    except Exception as e:
        print(f"DOB: Error loading blob {blob_name} from container {container_name}: {e}")
    return None

def save_json_to_blob(blob_name, data):
    """Save JSON content to an Azure Blob."""
    try:
        blob_client = blob_service_client.get_blob_client(container=ORGANISED_CONTAINER_NAME, blob=blob_name)
        blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True)
        print(f"DOB:Successfully updated {blob_name} in Azure Blob Storage.")
    except Exception as e:
        print(f"Error saving blob {blob_name}: {e}") 