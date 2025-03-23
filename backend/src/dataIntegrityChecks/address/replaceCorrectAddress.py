import json
import os
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
ORGANISED_CONTAINER_NAME = Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA

def replaceWithCorrectAddress(organised_output_blob_name, corrected_address_dict):
    try:
        # Read the JSON data from Azure Blob Storage
        data = load_json_from_blob(organised_output_blob_name, ORGANISED_CONTAINER_NAME)
        if data is None:
            print(f"Address: Error: Failed to load organized output from {organised_output_blob_name}.")
            return

        # Iterate over each key-value pair in the corrected_address_dict
        for original_address, corrected_address in corrected_address_dict.items():
            # Recursively search and replace addresses in the JSON data
            data = replace_address_in_json(data, original_address, corrected_address)
        
        # Save the modified data back to Azure Blob Storage
        save_json_to_blob(organised_output_blob_name, data)
        print("Addresses replaced successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def replace_address_in_json(data, original_address, corrected_address):
    """
    Recursively search for the original address in the JSON data and replace it with the corrected address.
    """
    if data is None:
        # Debug statement to log when data is None
        print("Encountered None value, skipping...")
        return None
    
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if value is None:
                # Log when encountering a None value within a dictionary
                print(f"None value found for key: {key}, skipping...")
                new_data[key] = None
            elif isinstance(value, (dict, list)):
                # Recursive call if the value is a dictionary or list
                new_data[key] = replace_address_in_json(value, original_address, corrected_address)
            elif isinstance(value, str) and original_address in value:
                # Replace the original address with the corrected address if it's found in a string
                print(f"Address:  Replacing '{original_address}' with '{corrected_address}' in key: {key}")
                new_data[key] = value.replace(original_address, corrected_address)
            else:
                # Just copy the value as it is if no replacement is needed
                new_data[key] = value
        return new_data
    elif isinstance(data, list):
        # If the data is a list, iterate over each element
        new_data = []
        for index, item in enumerate(data):
            if item is None:
                # Log when encountering a None value within a list
                print(f"None value found at index {index}, skipping...")
                new_data.append(None)
            elif isinstance(item, (dict, list)):
                # Recursive call for each element if it's a dictionary or list
                new_data.append(replace_address_in_json(item, original_address, corrected_address))
            elif isinstance(item, str) and original_address in item:
                # Replace the original address with the corrected address if it's found in a string
                print(f"Address:  Replacing '{original_address}' with '{corrected_address}' in list at index {index}")
                new_data.append(item.replace(original_address, corrected_address))
            else:
                # Just add the item as it is if no replacement is needed
                new_data.append(item)
        return new_data
    
    # Return data as-is if it's not a dict or list
    return data

def load_json_from_blob(organised_output_blob_name, container_name):
    """Load JSON content from an Azure Blob."""
    try:
        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=organised_output_blob_name)
        
        # Define the path for the downloaded file
        downloaded_file_path = os.path.join("/tmp", organised_output_blob_name)
        
        # Download the blob content to a temporary file
        with open(downloaded_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        # Read the downloaded file and parse the JSON content
        with open(downloaded_file_path, "r") as file:
            data = json.load(file)
        
        return data
    except json.JSONDecodeError as je:
        print(f"JSON decode error for blob {organised_output_blob_name}: {je}")
    except Exception as e:
        print(f"Address: Error loading blob {organised_output_blob_name} from container {container_name}: {e}")
    return None

def save_json_to_blob(organised_output_blob_name, data):
    """Save JSON content to an Azure Blob."""
    try:
        blob_client = blob_service_client.get_blob_client(container=ORGANISED_CONTAINER_NAME, blob=organised_output_blob_name)
        blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True)
        print(f"Address: Successfully updated {organised_output_blob_name} in Azure Blob Storage.")
    except Exception as e:
        print(f"Error saving blob {organised_output_blob_name}: {e}")