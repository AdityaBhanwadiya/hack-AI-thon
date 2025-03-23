import re

def standardize_phone_number(phone_number):
    # Remove all non-numeric characters
    cleaned_number = re.sub(r'\D', '', phone_number)
    
    # Check the length of the cleaned number
    if len(cleaned_number) == 10:
        # Format the number with the country code +1
        standardized_number = f"+1{cleaned_number}"
    elif len(cleaned_number) == 11 and cleaned_number.startswith('1'):
        # Handle cases where the number has a leading 1 and is 11 digits long
        standardized_number = f"+1{cleaned_number[1:]}"
    else:
        # Return number for numbers that do not meet the criteria
        standardized_number = cleaned_number

    return standardized_number


def updateTheListOfNumbers(phoneNumbersFromJS):
    # Create a new list to store updated phone numbers
    updated_numbers = []
    
    for number in phoneNumbersFromJS:
        updated_number = standardize_phone_number(number)
        updated_numbers.append(updated_number)
    
    return updated_numbers


