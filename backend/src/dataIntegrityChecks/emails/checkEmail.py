import json
import asyncio
import aiohttp
import os
import time
import uuid
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_EMAILS

# Asynchronous function to verify if an email exists using an email verification API
async def verify_email(session, email, api_key, max_retries=3, retry_delay=5):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
    retries = 0

    while retries < max_retries:
        try:
            async with session.get(url) as response:
                result = await response.json()

                if 'data' in result:
                    email_status = result['data'].get('status', '')
                    return email_status in ['valid', 'accept_all']
                elif 'errors' in result:
                    print(f"Error verifying {email}: {result['errors'][0]['details']}")
                    return False
                elif response.status == 202:
                    print(f"Verification still in progress for {email}, retrying in {retry_delay} seconds...")
                    retries += 1
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Unexpected response format for {email}: {result}")
                    return False
        except aiohttp.ClientError as e:
            print(f"HTTP error verifying {email}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error verifying {email}: {e}")
            return False

    print(f"Max retries reached for {email}. Verification could not be completed.")
    return False

# Function to load emails from a blob
async def load_emails_from_blob(blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        data = json.loads(blob_client.download_blob().readall())
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading emails from blob {blob_name}: {e}")
        return []

# Asynchronous function to verify emails in a blob and save results to a new blob
async def verify_emails_in_blob(input_blob_name, output_blob_name):
    api_key = Config.EMAIL_VERIFIER_API
    if not api_key:
        print("Error: API key not found in environment variables.")
        return None

    emails = await load_emails_from_blob(input_blob_name)
    if not emails:
        print(f"No emails found in {input_blob_name}.")
        return None

    verification_results = {}

    try:
        async with aiohttp.ClientSession() as session:
            tasks = [verify_email(session, email, api_key) for email in emails]
            results = await asyncio.gather(*tasks)

            for email, is_valid in zip(emails, results):
                verification_results[email] = is_valid
                status = "Valid" if is_valid else "Invalid"
                print(f"Email: {email}, Status: {status}")
    except Exception as e:
        print(f"Error during email verification: {e}")
        return None

    # Save verification results to a new blob
    try:
        save_results_to_blob(verification_results, output_blob_name)
    except Exception as e:
        print(f"Error saving results to {output_blob_name}: {e}")

    # Delete the temporary input blob after processing
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=input_blob_name)
        blob_client.delete_blob()
        print(f"Deleted temporary input blob: {input_blob_name}")
    except Exception as e:
        print(f"Error deleting input blob {input_blob_name}: {e}")

    return output_blob_name

# Function to save results to an Azure Blob
def save_results_to_blob(results, output_blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=output_blob_name)
        blob_client.upload_blob(json.dumps(results, indent=4), overwrite=True)
        print(f"Saved verified emails to Azure Blob: {output_blob_name}")
    except Exception as e:
        print(f"Error writing to blob {output_blob_name}: {e}")
