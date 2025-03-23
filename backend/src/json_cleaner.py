import json
import re
import backend.src.flatJson as flatJson

def clean_json_file(file_path: str):
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()
    

    # Remove any text before the JSON object
    content = extract_json_content(content)


    # # Check and remove backticks (assuming they are on separate lines)
    # if content.startswith("```json") and content.endswith("```"):
    #     content = content[7:-3].strip()
    
    # Attempt to sanitize problematic numeric formats like '75,900' to '75900'  
    content = re.sub(r'(?<=\d),(?=\d)', '', content)
    
    # Parse the JSON content
    try:
        json_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # Convert all values to strings
    json_data = convert_values_to_string(json_data)

    # Write the cleaned JSON back to the file
    with open(file_path, 'w') as file:
        json.dump(json_data, file, indent=4)

    print(f"Cleaned and converted JSON data saved to {file_path}")

def extract_json_content(content):
    """
    Extracts the JSON content from a text block that may contain extraneous text.
    
    Args:
    - content (str): The text content to extract JSON from.
    
    Returns:
    - str: The extracted JSON content.
    """
    # Use a regex pattern to find the JSON object
    json_pattern = re.compile(r'(\{.*\})', re.DOTALL)
    match = json_pattern.search(content)
    
    if match:
        return match.group(1)
    else:
        print("No valid JSON found in the content.")
        return '{}'
    
def convert_values_to_string(obj):
    if isinstance(obj, dict):
        return {k: convert_values_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_values_to_string(elem) for elem in obj]
    else:
        return str(obj)


# Example usage
# clean_json_file("organized_outputs/organized_data_f8e200ae-3324-473f-910c-09a71a25ec70.json")
