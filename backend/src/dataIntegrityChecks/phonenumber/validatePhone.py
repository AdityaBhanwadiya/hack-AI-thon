from twilio.rest import Client
import concurrent.futures
import requests  # To handle HTTP exceptions
from backend.src.config import Config

# Initialize Twilio client with your account SID and auth token
account_sid = Config.TWILIO_ACCOUNT_SID
auth_token = Config.TWILIO_AUTH_TOKEN

client = Client(account_sid, auth_token)

def validate_phone_number(phone_number):
    try:
        # Look up the phone number using Twilio's Lookup API
        phone_number_info = client.lookups \
            .phone_numbers(phone_number) \
            .fetch(type="carrier")
        
        # Check if the phone number is valid
        if phone_number_info and phone_number_info.carrier:
            return phone_number, True
        else:
            return phone_number, False
    except requests.exceptions.HTTPError as http_err:
        # Handle specific HTTP errors
        if http_err.response.status_code == 404:
            print(f"Phone number {phone_number} not found.")
            return phone_number, False
        else:
            print(f"HTTP error occurred for phone number {phone_number}: {http_err}")
            return phone_number, False
    except Exception as e:
        # Handle other potential exceptions
        print(f"Error validating phone number {phone_number}")
        return phone_number, False

def validate_phone_numbers_parallel(phone_numbers):
    results = {}
    
    # Use ThreadPoolExecutor to validate phone numbers in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit phone number validation tasks to the executor
        future_to_phone_number = {executor.submit(validate_phone_number, number): number for number in phone_numbers}
        
        # Process completed futures as they finish
        for future in concurrent.futures.as_completed(future_to_phone_number):
            try:
                phone_number, is_valid = future.result()
                results[phone_number] = is_valid
            except Exception as e:
                # Log any exceptions that occur during validation
                phone_number = future_to_phone_number[future]
                print(f"Error processing phone number {phone_number}: {e}")
                results[phone_number] = False
    print(results)
    return results
