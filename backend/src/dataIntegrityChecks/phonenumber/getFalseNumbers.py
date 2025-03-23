import backend.src.dataIntegrityChecks.phonenumber.standardizePhone  as standardizePhone

def get_invalid_phone_numbers(original_numbers, verified_numbers):
    # Create a mapping from standardized to original format
    original_format_mapping = {}

    # Standardize each number in the original list and map it to the original format
    for number in original_numbers:
        standardized_number = standardizePhone.standardize_phone_number(number)
        if standardized_number not in original_format_mapping:
            original_format_mapping[standardized_number] = number
    
    # Extract only the invalid numbers based on the verified_numbers dictionary
    invalid_numbers = [
        original_format_mapping[standardized]
        for standardized, is_valid in verified_numbers.items()
        if not is_valid and standardized in original_format_mapping
    ]
    
    return invalid_numbers
