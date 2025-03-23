import requests
from concurrent.futures import ThreadPoolExecutor
import time
from backend.src.config import Config

def check_address(address):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        'input': address,
        'key': Config.GOOGLE_API_KEY,
        'types': 'address',  # Restrict to address results
        'components': 'country:US'  # Optional: Restrict to US addresses
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    if data.get('status') != 'OK' or not data.get('predictions'):
        print(f"No place ID found for {address} | Response: {data}")
        return None

    place_id = data['predictions'][0]['place_id']
    print(f"✅ Found Place ID for '{address}': {place_id}")
    return place_id

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'key': Config.GOOGLE_API_KEY,
        'fields': 'formatted_address'  # Request only formatted_address
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    if data.get('status') != 'OK':
        print(f"Error fetching details for {place_id} | Response: {data}")
        return None

    formatted_address = data['result'].get('formatted_address')
    if not formatted_address:
        print(f"No formatted address for {place_id} | Response: {data}")
        return None

    print(f"✅ Updated Address: {formatted_address}")
    return formatted_address

def validate_single_address(address):
    place_id = check_address(address)
    if place_id:
        corrected_address = get_place_details(place_id)
        if corrected_address:
            return (address, corrected_address)
        else:
            return (address, "Invalid address (Place Details failed)")
    else:
        return (address, "Invalid address (Autocomplete failed)")

def validationHandler(addresses):
    corrected_address_dict = {}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(validate_single_address, addresses)

    end_time = time.time()
    
    for original_address, corrected_address in results:
        corrected_address_dict[original_address] = corrected_address

    duration = end_time - start_time
    print(f"⏳ Time taken: {duration:.2f} seconds")
    
    return corrected_address_dict