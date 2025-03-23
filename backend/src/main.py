# import os
# import uuid
# import asyncio
# from flask import Flask, request, render_template
# from werkzeug.utils import secure_filename
# from azure.storage.blob import BlobServiceClient
# from config import Config
# from document_processor import DocumentProcessor
# from data_organizer import DocumentOrganizer

# # Set base directories and template folder
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../frontend"))
# app = Flask(__name__, template_folder=TEMPLATE_DIR)

# # Initialize Azure Blob Service Client
# blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

# # Initialize Document Processor and Organizer
# doc_processor = DocumentProcessor(Config.AZURE_FORM_RECOGNIZER_ENDPOINT, Config.AZURE_FORM_RECOGNIZER_KEY)
# doc_organizer = DocumentOrganizer(Config.AZURE_OPENAI_ENDPOINT, Config.AZURE_OPENAI_KEY,
#                                   Config.AZURE_OPENAI_API_VERSION, Config.AZURE_OPENAI_API_TYPE)

# @app.route("/", methods=["GET"])
# def home():
#     return render_template("upload.html")

# @app.route("/upload", methods=["POST"])
# def upload_file():
#     if "file" not in request.files:
#         return "No file part", 400

#     file = request.files["file"]

#     if file.filename == "":
#         return "No selected file", 400

#     if file:
#         filename = secure_filename(file.filename)
#         unique_filename = f"{filename}_{uuid.uuid4()}"
#         blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_BLOB, blob=unique_filename)
        
#         # Upload the file to Azure Blob Storage
#         blob_client.upload_blob(file)

#         # Download the file from Azure Blob Storage to a local /tmp path
#         download_file_path = os.path.join("/tmp", filename)
#         with open(download_file_path, "wb") as download_file:
#             download_file.write(blob_client.download_blob().readall())

#         # Process the document using DocumentProcessor
#         extracted_text = doc_processor.extract_text_from_document(download_file_path)

#         # Upload the extracted text to the extracted text container
#         extracted_blob_filename = f"extracted_{uuid.uuid4()}.txt"
#         extracted_blob_client = blob_service_client.get_blob_client(
#             container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_TEXT_FILE, blob=extracted_blob_filename)
#         extracted_blob_client.upload_blob(extracted_text)

#         # Process and organize the document
#         asyncio.run(process_and_organize_document(extracted_blob_filename))

#         return render_template("success.html", file_name=file.filename)

#     return render_template("upload.html")

# async def process_and_organize_document(extracted_blob_filename):
#     # Ensure we work in /tmp so that file names match what we pass as blob names
#     os.chdir("/tmp")
    
#     # Download the extracted text file from blob storage to /tmp
#     extracted_blob_client = blob_service_client.get_blob_client(
#         container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_TEXT_FILE, blob=extracted_blob_filename)
#     download_extracted_file_path = os.path.join("/tmp", extracted_blob_filename)
#     with open(download_extracted_file_path, "wb") as download_file:
#         download_file.write(extracted_blob_client.download_blob().readall())

#     # Generate a blob name and use it (without the /tmp prefix)
#     json_output_filename = f"organized_{uuid.uuid4()}.json"
#     # Note: process_document will create the file locally using the provided blob name
#     await doc_organizer.process_document(download_extracted_file_path, json_output_filename)
    
#     print("Saved to organized file named: " + json_output_filename)

# if __name__ == "__main__":
#     app.run(debug=True)


import os
import uuid
import asyncio
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config
from backend.src.document_processor import DocumentProcessor
from backend.src.data_organizer import DocumentOrganizer

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

# Initialize Document Processor
doc_processor = DocumentProcessor(Config.AZURE_FORM_RECOGNIZER_ENDPOINT, Config.AZURE_FORM_RECOGNIZER_KEY)

# Initialize Document Organizer
doc_organizer = DocumentOrganizer(Config.AZURE_OPENAI_ENDPOINT, Config.AZURE_OPENAI_KEY, Config.AZURE_OPENAI_API_VERSION, Config.AZURE_OPENAI_API_TYPE)

async def process_and_organize_document(extracted_blob_filename):
    # Download the extracted text file from Azure Blob Storage
    extracted_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_TEXT_FILE, blob=extracted_blob_filename)
    download_extracted_file_path = os.path.join("/tmp", extracted_blob_filename)
    with open(download_extracted_file_path, "wb") as download_file:
        download_file.write(extracted_blob_client.download_blob().readall())

    # Define the path for the organized JSON file
    json_output_filename = f"organized_{uuid.uuid4()}.json"

    # Process the document using DocumentOrganizer asynchronously
    await doc_organizer.process_document(download_extracted_file_path, json_output_filename)

    # Upload the organized JSON file to the organizedfiles container
    organized_blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA, blob=json_output_filename)
    with open(json_output_filename, "rb") as data:
        organized_blob_client.upload_blob(data)

    print(f"Saved to organized file named: {json_output_filename}")
