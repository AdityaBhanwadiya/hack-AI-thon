import json
import re
import os
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS
ORGANISED_CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA

def replace_emails_in_blob(organised_output_blob_name, verification_results_blob_name):
    # Load verification results from Azure Blob Storage
    verification_data = load_json_from_blob(verification_results_blob_name, CONTAINER_NAME)
    if verification_data is None:
        print(f"Error: Failed to load verification results from {verification_results_blob_name}.")
        return

    # Get the list of emails that need to be replaced
    emails_to_replace = set(verification_data.keys())

    # Load the organized output file from Azure Blob Storage
    content = load_json_from_blob(organised_output_blob_name, ORGANISED_CONTAINER_NAME)
    if content is None:
        print(f"Error: Failed to load organized output from {organised_output_blob_name}.")
        return

    # Replace occurrences of emails with "I CAN'T READ THIS"
    updated_content = json.dumps(content)  # Convert JSON object to a string
    for email in emails_to_replace:
        updated_content = re.sub(rf'\b{re.escape(email)}\b', "I CAN'T READ THIS", updated_content)

    # Convert string back to JSON
    updated_json_content = json.loads(updated_content)

    # Save the updated JSON back to the Azure Blob Storage
    save_json_to_blob(organised_output_blob_name, updated_json_content)
    print(f"Updated {organised_output_blob_name} with replacements.")

     # Delete the intermediate blob from the extracted emails container
    delete_blob(verification_results_blob_name, CONTAINER_NAME)
    print(f"Deleted intermediate blob {verification_results_blob_name} from {CONTAINER_NAME}.")


def load_json_from_blob(blob_name, container_name):
    """Load JSON content from an Azure Blob."""
    try:
        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Define the path for the downloaded file
        downloaded_file_path = os.path.join("/tmp", blob_name)

        print(f"Downloading blob to: {downloaded_file_path}")

        
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
        print(f"Error loading blob {blob_name} from container {container_name}: {e}")
    return None


def save_json_to_blob(blob_name, data):
    """Save JSON content to an Azure Blob."""
    try:
        blob_client = blob_service_client.get_blob_client(container=ORGANISED_CONTAINER_NAME, blob=blob_name)
        blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True)
        print(f"Successfully updated {blob_name} in Azure Blob Storage.")
    except Exception as e:
        print(f"Error saving blob {blob_name}: {e}")


def delete_blob(blob_name, container_name):
    """Delete a blob from an Azure Blob container."""
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.delete_blob()
        print(f"Successfully deleted {blob_name} from {container_name}.")
    except Exception as e:
        print(f"Error deleting blob {blob_name} from container {container_name}: {e}")