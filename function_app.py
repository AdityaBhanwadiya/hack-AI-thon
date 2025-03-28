import os
import uuid
import asyncio
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from backend.src.config import Config
from backend.src.document_processor import DocumentProcessor
from backend.src.data_organizer import DocumentOrganizer
from azure.storage.blob import generate_container_sas, ContainerSasPermissions
from datetime import datetime, timedelta
from backend.src.notify import notify_status



# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

# Initialize Document Processor and Organizer
doc_processor = DocumentProcessor(Config.AZURE_FORM_RECOGNIZER_ENDPOINT, Config.AZURE_FORM_RECOGNIZER_KEY)
doc_organizer = DocumentOrganizer(
    Config.AZURE_OPENAI_ENDPOINT,
    Config.AZURE_OPENAI_KEY,
    Config.AZURE_OPENAI_API_VERSION,
    Config.AZURE_OPENAI_API_TYPE
)

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="newblobstorage/{name}",
                               connection="newincomingblobstorage_STORAGE") 
def IncomingBlobStorage(myblob: func.InputStream):
    logging.info(f"Blob trigger fired for blob: {myblob.name}")

    try:
        original_file_name = os.path.basename(myblob.name)
        filename_only = f"renamed_{uuid.uuid4()}_{original_file_name}"
        raw_file_path = os.path.join("/tmp", filename_only)

        with open(raw_file_path, "wb") as f:
            f.write(myblob.read())
        logging.info(f"Saved raw file to: {raw_file_path}")
        notify_status(f"Reading your docuement...")

        # Extract text from the document using DocumentProcessor
        extracted_text = doc_processor.extract_text_from_document(raw_file_path)
        if not extracted_text:
            logging.error(f"Failed to extract text from {raw_file_path}")
            return

        # Create a unique name for the extracted text file and upload it
        extracted_blob_filename = f"extracted_{uuid.uuid4()}.txt"

        extracted_blob_client = blob_service_client.get_blob_client(
            container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_TEXT_FILE,
            blob=extracted_blob_filename
        )
        extracted_blob_client.upload_blob(extracted_text)
        logging.info(f"Uploaded extracted text as blob: {extracted_blob_filename}")

        # Process and organize the document based on the extracted text file
        asyncio.run(process_and_organize_document(extracted_blob_filename))

    except Exception as e:
        logging.error(f"Error in IncomingBlobTrigger: {str(e)}")


async def process_and_organize_document(extracted_blob_filename):
    try:
        # Download the extracted text file from its blob container to a local file
        extracted_blob_client = blob_service_client.get_blob_client(
            container=Config.AZURE_CONTAINER_NAME_FOR_EXTRACTED_TEXT_FILE,
            blob=extracted_blob_filename
        )
        download_extracted_file_path = os.path.join("/tmp", extracted_blob_filename)
        with open(download_extracted_file_path, "wb") as download_file:
            download_file.write(extracted_blob_client.download_blob().readall())
        logging.info(f"Downloaded extracted text file to: {download_extracted_file_path}")

        # Define the output file name for the organized JSON file
        json_output_filename = f"organized{uuid.uuid4()}.json"

        # Process the document using DocumentOrganizer asynchronously
        await doc_organizer.process_document(download_extracted_file_path, json_output_filename)
        logging.info(f"Document processing complete. Organized file: {json_output_filename}")

        # Upload the organized JSON file to the organized data container
        organized_blob_client = blob_service_client.get_blob_client(
            container=Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA,
            blob=json_output_filename
        )
        with open(json_output_filename, "rb") as data:
            organized_blob_client.upload_blob(data)
        logging.info(f"Uploaded organized file to blob container as: {json_output_filename}")

    except Exception as e:
        logging.error(f"Error in process_and_organize_document: {str(e)}")

@app.route(route="generateToken", auth_level=func.AuthLevel.ANONYMOUS)
def generateToken(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Generating SAS token...')
    notify_status("Generating your identity for us...")

    account_name = Config.AZURE_STORAGE_ACCOUNT_NAME
    account_key = Config.AZURE_STORAGE_ACCOUNT_KEY
    container_name = Config.AZURE_CONTAINER_NAME_FOR_BLOB

    if not all([account_name, account_key, container_name]):
        return func.HttpResponse("Missing environment variables", status_code=500)

    try:
        sas_token = generate_container_sas(
            account_name=account_name,
            container_name=container_name,
            account_key=account_key,
            permission=ContainerSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(minutes=30)
        )

        return func.HttpResponse(
            body=json_response({
                "sasToken": sas_token,
                "containerName": container_name,
                "accountName": account_name
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error generating SAS token: {e}")
        return func.HttpResponse("Failed to generate SAS token", status_code=500)

def json_response(data):
    import json
    return json.dumps(data)



@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS)
@app.generic_input_binding(
    arg_name="connectionInfo",
    type="signalRConnectionInfo",
    hub_name="chat",
    connection="AzureSignalRConnectionString",
    data_type="string"
)
def negotiate(req: func.HttpRequest, connectionInfo: str) -> func.HttpResponse:
    try:
        if not connectionInfo:
            logging.error("No connectionInfo returned from SignalR binding.")
            return func.HttpResponse("Binding failed to produce connection info.", status_code=500)
        logging.info("Successfully retrieved connectionInfo.")
        return func.HttpResponse(connectionInfo, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error in negotiate function: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.route(route="send_message", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_output_binding(
    arg_name="signalRMessages", 
    type="signalR",
    hub_name="chat",
    connection="AzureSignalRConnectionString"
)
def send_message(req: func.HttpRequest, signalRMessages) -> func.HttpResponse:
    try:
        logging.info(f"HTTP method: {req.method}")
        logging.info(f"Content-Type: {req.headers.get('Content-Type')}")
        raw_body = req.get_body()
        logging.info(f"Raw body: {raw_body}")

        # Parse JSON
        body = req.get_json()
        message = body.get("message", "Processing...")

        logging.info(f"Parsed message: {message}")

        signalRMessages.set([
            {
                "target": "statusMessage",
                "arguments": [message]
            }
        ])

        return func.HttpResponse("SignalR message sent.", status_code=200)

    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
