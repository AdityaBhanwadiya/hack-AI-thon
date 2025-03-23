import json
import os
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
ORGANISED_CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA

def replaceNumber(organised_output_blob_name, verifiedPhoneNumbers):
    # Load the organized output JSON data from Azure Blob Storage
    content = load_json_from_blob(organised_output_blob_name, ORGANISED_CONTAINER_NAME)
    if content is None:
        print(f"Phone: Error: Failed to load organized output from {organised_output_blob_name}.")
        return

    # Iterate through the verified phone numbers list
    for invalid_number in verifiedPhoneNumbers:
        # Find and replace invalid phone numbers in the JSON data
        for key, value in content.items():
            if value == invalid_number:
                content[key] = "I CAN'T READ THIS"
            elif isinstance(value, dict):  # If value is a nested dictionary
                for subkey, subvalue in value.items():
                    if subvalue == invalid_number:
                        value[subkey] = "I CAN'T READ THIS"
            elif isinstance(value, list):  # If value is a list
                for i, item in enumerate(value):
                    if item == invalid_number:
                        value[i] = "I CAN'T READ THIS"

    # Save the updated JSON data back to Azure Blob Storage
    save_json_to_blob(organised_output_blob_name, content)
    print(f"Phone: Updated {organised_output_blob_name} with replacements.")

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
        print(f"Phone: Error loading blob {blob_name} from container {container_name}: {e}")
    return None

def save_json_to_blob(blob_name, data):
    """Save JSON content to an Azure Blob."""
    try:
        blob_client = blob_service_client.get_blob_client(container=ORGANISED_CONTAINER_NAME, blob=blob_name)
        blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True)
        print(f"Phone: Successfully updated {blob_name} in Azure Blob Storage.")
    except Exception as e:
        print(f"Error saving blob {blob_name}: {e}")