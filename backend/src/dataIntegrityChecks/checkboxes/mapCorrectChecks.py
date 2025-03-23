import json
import os
from config import Config
from document_processor import DocumentProcessor

document_analysis_client = DocumentProcessor(endpoint=Config.AZURE_ENDPOINT, api_key=Config.AZURE_API_KEY)

# # Function to calculate the distance between two points
# def calculate_distance(point1, point2):
#     return ((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2) ** 0.5

# # Function to find the nearest text to a checkbox
# def find_nearest_text(selection_mark, text_elements):
#     closest_text = None
#     min_distance = float('inf')

#     for text in text_elements:
#         distance = calculate_distance(selection_mark.polygon[0], text.polygon[0])
#         if distance < min_distance and abs(selection_mark.polygon[0].y - text.polygon[0].y) < 20:
#             min_distance = distance
#             closest_text = text

#     return closest_text

# def mapCorrectChecks(image_path):
#     # Process the document
#     result = document_analysis_client.process_document(image_path)

#     # Dictionary to store results
#     results = {}

#     # Loop through the analyzed document pages
#     for page in result.pages:
#         print(f"Page number: {page.page_number}")
        
#         # Get all text elements on the page
#         text_elements = page.lines  # or page.words for more granularity

#         # Loop through selection marks (checkboxes) on the page
#         for i, selection_mark in enumerate(page.selection_marks):
#             checkbox_state = selection_mark.state
#             checkbox_location = selection_mark.polygon
            
#             # Find the closest text to the checkbox
#             nearest_text = find_nearest_text(selection_mark, text_elements)
            
#             # Process the checkbox state and field name
#             if nearest_text:
#                 field_name = nearest_text.content  # the text near the checkbox
#                 print(field_name)
#             else:
#                 results[checkbox_location] = (checkbox_state == 'selected')

#     # Define the output path for the JSON file
#     output_path = os.path.join('mapping', 'checkbox_mapping.json')

#     # Ensure the mapping folder exists
#     os.makedirs('mapping', exist_ok=True)

#     # Write results to a JSON file
#     with open(output_path, "w") as json_file:
#         json.dump(results, json_file, indent=4)

#     print("Results have been written to mapping/checkbox_mapping.json")



# Function to calculate the centroid of a polygon
def calculate_centroid(polygon):
    x_coords = [point.x for point in polygon]
    y_coords = [point.y for point in polygon]
    centroid_x = sum(x_coords) / len(polygon)
    centroid_y = sum(y_coords) / len(polygon)
    return centroid_x, centroid_y

# Modified function to calculate distance using centroids
def calculate_distance(point1, point2):
    centroid1 = calculate_centroid(point1)
    centroid2 = calculate_centroid(point2)
    return ((centroid1[0] - centroid2[0]) ** 2 + (centroid1[1] - centroid2[1]) ** 2) ** 0.5

# Function to find the nearest text to a checkbox
def find_nearest_text(selection_mark, text_elements):
    closest_text = None
    min_distance = float('inf')
    
    # Calculate the centroid of the selection mark polygon
    selection_centroid = calculate_centroid(selection_mark.polygon)

    for text in text_elements:
        # Calculate the distance between the checkbox and text centroid
        text_centroid = calculate_centroid(text.polygon)
        distance = calculate_distance(selection_mark.polygon, text.polygon)
        
        # Consider text lines that are horizontally aligned within a threshold
        if distance < min_distance and abs(selection_centroid[1] - text_centroid[1]) < 20:
            min_distance = distance
            closest_text = text

    return closest_text

def mapCorrectChecks(image_path):
    # Process the document
    result = document_analysis_client.process_document(image_path)

    # Dictionary to store results
    results = {}

    # Loop through the analyzed document pages
    for page in result.pages:
        print(f"Page number: {page.page_number}")
        
        # Get all text elements on the page
        text_elements = page.words  # Use words for more granularity

        # Loop through selection marks (checkboxes) on the page
        for selection_mark in page.selection_marks:
            checkbox_state = selection_mark.state
            checkbox_location = selection_mark.polygon
            
            # Find the closest text to the checkbox
            nearest_text = find_nearest_text(selection_mark, text_elements)
            
            # Process the checkbox state and field name
            if nearest_text:
                field_name = nearest_text.content  # the text near the checkbox
                results[field_name] = (checkbox_state == 'selected')
                print(f"Field: {field_name}, State: {checkbox_state}")
            else:
                results[str(checkbox_location)] = (checkbox_state == 'selected')

    # Define the output path for the JSON file
    output_path = os.path.join('mapping', 'checkbox_mapping.json')

    # Ensure the mapping folder exists
    os.makedirs('mapping', exist_ok=True)

    # Write results to a JSON file
    with open(output_path, "w") as json_file:
        json.dump(results, json_file, indent=4)

    print("Results have been written to mapping/checkbox_mapping.json")
