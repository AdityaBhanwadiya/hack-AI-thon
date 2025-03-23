import json
import re

def flatten_json(file_path, parent_key='', sep='.'):
    # Read and parse the JSON content from the file
    with open(file_path, 'r') as file:
        json_data = json.load(file)

    # Helper function to flatten the JSON, including handling lists
    def flatten(json_obj, parent_key='', sep='.'):
        items = []
        if isinstance(json_obj, dict):
            for k, v in json_obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        items.extend(flatten(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((new_key, v))
        elif isinstance(json_obj, list):
            for i, item in enumerate(json_obj):
                items.extend(flatten(item, f"{parent_key}{sep}{i}", sep=sep).items())
        else:
            items.append((parent_key, json_obj))
        return dict(items)

    # Flatten the JSON data
    flattened_json = flatten(json_data, parent_key, sep)

    # Write the flattened JSON back to the file
    with open(file_path, 'w') as file:
        json.dump(flattened_json, file, indent=4)