import os
import uuid
import sys

# Modify sys.path to access config file in the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from document_processor import DocumentProcessor
from config import Config

# Initialize the Azure Document Processor
doc_processor = DocumentProcessor(endpoint=Config.AZURE_ENDPOINT, api_key=Config.AZURE_API_KEY)

# Define the folder where the PDF is located
pdf_folder = os.path.join("scripts", "dataIntegrityChecks", Config.BANK_PDF_FOLDER)

data_file_path = "scripts/dataIntegrityChecks/equipmentRefs/banks_list.pdf"

# Check if the file exists
if os.path.exists(data_file_path):
    # Process the document with Azure Form Recognizer
    output_filename = f"bank_names_data_{uuid.uuid4()}.txt"
    output_file_path = os.path.join(pdf_folder, output_filename)

    # Process the document and extract data
    result = doc_processor.process_document(data_file_path)

    # Debug: Check how many pages are processed
    print(f"Total pages processed: {len(result.pages)}")

    # Save the extracted data to a file in the same folder
    with open(output_file_path, "w") as output_file:
        for page in result.pages:
            output_file.write(f"Page number: {page.page_number}\n")
            output_file.write("\nText Lines:\n")
            for line in page.lines:
                output_file.write(f"{line.content}\n")

    print(f"Processed data saved to {output_file_path}")
else:
    print(f"File {data_file_path} not found")
