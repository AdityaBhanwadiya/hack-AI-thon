import json
import re
import asyncio
import aiohttp
import os
import uuid
from azure.storage.blob import BlobServiceClient
from backend.src.dataIntegrityChecks.emails import checkEmail as checkEmail
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

# Function to recursively search for email addresses in a nested JSON structure
def extract_emails_from_json(data, parent_key=''):
    emails = {}  # Use a dictionary to store email addresses and their keys
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            # If value is a dictionary or list, recurse into it
            if isinstance(value, (dict, list)):
                emails.update(extract_emails_from_json(value, new_key))
            else:
                # If value is a string, search for emails
                found_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", str(value))
                if found_emails:
                    for email in found_emails:
                        emails[new_key] = email
    elif isinstance(data, list):
        for i, item in enumerate(data):
            # Use list index as part of parent_key for list items
            emails.update(extract_emails_from_json(item, f"{parent_key}[{i}]"))
    
    print(emails)
    return emails

# Function to process a single JSON file and extract emails
async def extract_emails_from_json_file(file_path):
    all_emails = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            all_emails.update(extract_emails_from_json(data))
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {file_path}.")
    except UnicodeDecodeError:
        print(f"Error: Failed to decode {file_path} due to encoding issues.")
    except Exception as e:
        print(f"Unexpected error occurred while reading {file_path}: {e}")

    # Directly pass the dictionary of emails to the verification function
    verification_results = await verify_emails(all_emails)
    return verification_results

# Verify emails and save results to a file
async def verify_emails(emails):
    # Generate a unique identifier for the files
    unique_id = uuid.uuid4().hex
    temp_emails_blob_name = f'temp_extractedEmails_{unique_id}.json'
    temp_emails_only_blob_name = f'temp_emails_only_{unique_id}.json'
    verified_emails_blob_name = f'verifiedEmails_{unique_id}.json'

    try:
        # Save the emails to a temporary blob with a unique name
        temp_emails_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS, blob=temp_emails_blob_name)
        temp_emails_blob_client.upload_blob(json.dumps(emails))
    except Exception as e:
        print(f"Unexpected error occurred while uploading temporary extracted emails to {temp_emails_blob_name}: {e}")

    # Extract only the email addresses from the temp_emails_blob
    email_addresses = list(emails.values())
    try:
        temp_emails_only_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS, blob=temp_emails_only_blob_name)
        temp_emails_only_blob_client.upload_blob(json.dumps(email_addresses))
    except Exception as e:
        print(f"Unexpected error occurred while uploading email addresses to {temp_emails_only_blob_name}: {e}")

    # Call the verification function using the blob with email addresses only
    verification_results = await checkEmail.verify_emails_in_blob(temp_emails_only_blob_name, verified_emails_blob_name)

    await update_verification_results(temp_emails_blob_name, verification_results)
    # Remove the temporary blobs after verification
    try:
        temp_emails_blob_client.delete_blob()
    except Exception as e:
        print(f"Error removing temporary blob {temp_emails_blob_name}: {e}")

    return verification_results


async def update_verification_results(temp_emails_blob_name, verification_results_blob_name):
    # Download the temp_emails_blob
    try:
        temp_emails_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS, blob=temp_emails_blob_name)
        temp_emails_data = json.loads(temp_emails_blob_client.download_blob().readall())
    except Exception as e:
        print(f"Unexpected error occurred while downloading {temp_emails_blob_name}: {e}")
        return

    # Download the verification_results_blob
    try:
        verification_results_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS, blob=verification_results_blob_name)
        verification_results = json.loads(verification_results_blob_client.download_blob().readall())
    except Exception as e:
        print(f"Unexpected error occurred while downloading {verification_results_blob_name}: {e}")
        return

    # Create a dictionary to store only the emails with false results
    filtered_results = {email: result for email, result in verification_results.items() if not result}

    # Write the filtered results back to the verification_results_blob
    try:
        verification_results_blob_client.upload_blob(json.dumps(filtered_results), overwrite=True)
        print(f"Updated {verification_results_blob_name} with false results.")
    except Exception as e:
        print(f"Unexpected error occurred while uploading to {verification_results_blob_name}: {e}")

