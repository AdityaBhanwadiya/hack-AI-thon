import json
import re
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config
import backend.src.dataIntegrityChecks.address.validateAddress as validateAddress

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

def is_strictly_alphanumeric(string):
    # Check if the string contains only letters, digits, and spaces
    return all(char.isalnum() or char.isspace() for char in string)

def extract_addresses(json_data):
    addresses = []
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, dict):
                addresses.extend(extract_addresses(value))
            elif isinstance(value, list):
                for item in value:
                    addresses.extend(extract_addresses(item))
            elif isinstance(value, str):
                if 'address' in key.lower():  # Check if 'address' is in the key
                    if value.strip():  # Check if the value is not an empty string
                        addresses.append(value.strip())
    
    unique_addresses = set(addresses)  # Ensure uniqueness
    
    # Filter out addresses that are not strictly alphanumeric
    filtered_addresses = [addr for addr in unique_addresses if not is_strictly_alphanumeric(addr)]
    
    print("Address: Filtered list of unique strictly alphanumeric addresses:")
    print(filtered_addresses)

    print("Address: Sending the filtered list of addresses for validation...")

    corrected_address_dict = validateAddress.validationHandler(filtered_addresses)

    print("Address: Got the Validated results, sending ahead...")
    return corrected_address_dict

def read_json_from_blob(blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA, blob=blob_name)
        blob_data = blob_client.download_blob().readall()
        data = json.loads(blob_data)
        return data
    except FileNotFoundError:
        print(f"Address: Blob not found: {blob_name}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error for blob {blob_name}: {e}")
    except Exception as e:
        print(f"Address: Error reading blob {blob_name}: {e}")
    return None

def process_addresses_from_blob(blob_name):
    json_data = read_json_from_blob(blob_name)
    if json_data is not None:
        corrected_address_dict = extract_addresses(json_data)
    else:
        print(f"Address: Failed to process addresses from {blob_name}")

    return corrected_address_dict