import os
import openai
import json
import asyncio
import time
from backend.src.config import Config
import backend.src.json_cleaner as json_cleaner
from azure.storage.blob import BlobServiceClient
import backend.src.flatJson as flatJson
# Email checks
from backend.src.dataIntegrityChecks.emails import replaceWrongEmails
from backend.src.dataIntegrityChecks.emails import extractEmailProcessor

# Date of Birth checks
from backend.src.dataIntegrityChecks.dateofbirth import extractDOBProcessor
from backend.src.dataIntegrityChecks.dateofbirth import replaceWrongDOBs

# Phone number checks
from backend.src.dataIntegrityChecks.phonenumber import extractPhoneProcessor
from backend.src.dataIntegrityChecks.phonenumber import standardizePhone
from backend.src.dataIntegrityChecks.phonenumber import validatePhone
from backend.src.dataIntegrityChecks.phonenumber import replaceWrongPhoneNumbers
from backend.src.dataIntegrityChecks.phonenumber import getFalseNumbers

# Address checks
from backend.src.dataIntegrityChecks.address import extractAddress
from backend.src.dataIntegrityChecks.address import replaceCorrectAddress

class DocumentOrganizer:
    def __init__(self, openai_endpoint, openai_key, api_version="2024-02-01-preview", api_type="azure"):
        self.openai_endpoint = openai_endpoint
        self.openai_key = openai_key
        openai.api_type = api_type
        openai.api_base = openai_endpoint
        openai.api_version = api_version
        openai.api_key = openai_key

    async def process_document(self, text_file, organised_output_file_path):

        # Process the text
        start_time = time.time()
        """
        Reads extracted text, processes it using Azure OpenAI Foundry, and saves JSON output.
        """
        with open(text_file, "r") as f:
            extracted_text = f.read()

        fileName = organised_output_file_path.split('.')[0]

        # ✅ Using the exact same prompt from your original code
        prompt = f"""
        Extract structured data from the following document:
        {extracted_text}

        Format:
        {{
            (
            "Follow this structure precisely:"
            "\n"
            "  \"File Name\": \"{fileName}\",\n"
            "  \"Financing Company Name\": \"\",\n"
            "  \"Financing Company Address\": \"\",\n"
            "  \"Financing Company 1 Person to Contact\": \"\",\n"
            "  \"Financing Company 1 Phone\": \"\",\n"
            "  \"Financing Company 1 Fax\": \"\",\n"
            "  \"Financing Company 1 Email\": \"\",\n"
            "\n"
            "  \"Dealer Name/Company\": \"\",\n"
            "  \"Dealer Address\": \"\",\n"
            "  \"Dealer Phone\": \"\",\n"
            "  \"Dealer Email\": \"\",\n"
            "  \"Dealer Contact\": \"\",\n"
            "\n"
            "  \"Applicant/Business Legal Name\": \"\",\n"
            "  \"Applicant/Business Operating Name/DBA\": \"\",\n"
            "  \"Applicant/Business Address\": \"\",\n"
            "  \"Applicant/Business Billing Address\": \"\",\n"
            "  \"Applicant/Business Physical Address\": \"\",\n"
            "  \"Applicant/Business Vehicle Address\": \"\",\n"
            "  \"Applicant/Business Phone\": \"\",\n"
            "  \"Applicant/Business Email\": \"\",\n"
            "  \"Applicant/Business Primary Contact\": \"\",\n"
            "  \"Applicant/Business Primary Contact Phone\": \"\",\n"
            "  \"Applicant/Business Primary Contact Email\": \"\",\n"
            "  \"Applicant/Business Structure\": \"\",\n"
            "  \"Applicant/Business Annual Revenue\": \"\",\n"
            "  \"Applicant/Business Established In\": \"\",\n"
            "  \"Applicant/Business Number of years in Business\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Name\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Title\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 DOB\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Address\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Ownership\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Home Phone\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Cell Phone\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Email\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Country of Citizenship\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Years with Company\": \"\",\n"
            "  \"Applicant/Business Owner/Guarantor/Principal No. 1 Declared Bankruptcy\": \"\",\n"
            "\n"
            "  \"Equipment Supplier\": \"\",\n"
            "  \"Equipment Sales Rep\": \"\",\n"
            "  \"Equipment 1 Manufacturer\": \"\",\n"
            "  \"Equipment 1 Make\": \"\",\n"
            "  \"Equipment 1 Model\": \"\",\n"
            "  \"Equipment 1 Condition\": \"\",\n"
            "  \"Equipment 1 Specifications\": \"\",\n"
            "  \"Equipment 1 Category\": \"\",\n"
            "  \"Equipment 1 Type\": \"\",\n"
            "  \"Equipment 1 Age\": \"\",\n"
            "  \"Equipment 1 Purpose\": \"\",\n"
            "  \"Hauling References/Major Customer 1 Company Name\": \"\",\n"
            "  \"Hauling References/Major Customer 1 Company Contact\": \"\",\n"
            "  \"Hauling References/Major Customer 1 Company Phone Number\": \"\",\n"
            "  \"Credit References/Business References 1 Name\": \"\",\n"
            "  \"Credit References/Business References 1 Account Number\": \"\",\n"
            "  \"Credit References/Business References 1 Phone\": \"\",\n"
            "  \"Credit References/Business References 1 Contact\": \"\"\n"
        )
        }}
        """

        client = openai.AzureOpenAI(
            api_key=self.openai_key,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=self.openai_endpoint
        )
        response = client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a highly skilled assistant tasked with organizing the extracted text data into key-value pairs. Ensure that the output is in JSON format. "
                                                "Follow the given structure precisely, making sure to separate business, guarantor, and reference details appropriately. "
                                                "If a field is missing, leave it blank instead of omitting it."},
                    {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        structured_data = response.choices[0].message.content

        # Save the response to the text file
        with open(organised_output_file_path, "w") as file:
           file.write(structured_data)

        print(f"Organized data saved to {organised_output_file_path}")



        json_cleaner.clean_json_file(organised_output_file_path)
        flatJson.flatten_json(organised_output_file_path)



        ############# Save the organized to Container First ################
        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)

        # upload the organized JSON file to the organized data container using the same blob name.
        organized_blob_client = blob_service_client.get_blob_client(
            container=Config.AZURE_CONTAINER_NAME_FOR_ORGANIZED_DATA, blob=organised_output_file_path)
        with open(organised_output_file_path, "rb") as data:
            organized_blob_client.upload_blob(data, overwrite=True)


        # Run data integrity checks asynchronously
        await asyncio.gather(
            validate_email(organised_output_file_path),
            validate_dob(organised_output_file_path),
            validate_phone(organised_output_file_path),
            validate_address(organised_output_file_path)
        )

        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Time taken in seconds:", elapsed_time)

        return organised_output_file_path

async def validate_email(organised_output_file_path):
    try:
        verification_results_file = await extractEmailProcessor.extract_emails_from_json_file(organised_output_file_path)
        replaceWrongEmails.replace_emails_in_blob(organised_output_file_path, verification_results_file)
    except Exception as e:
        print(f"Error during email validation: {e}")

async def validate_dob(organised_output_file_path):
    try:
        wrongFormattedDOBSet = extractDOBProcessor.extract_dob_from_file(organised_output_file_path)
        replaceWrongDOBs.replace_dob_in_blob(organised_output_file_path, wrongFormattedDOBSet)
    except Exception as e:
        print(f"Error during DOB validation: {e}")

async def validate_phone(organised_output_file_path):
    try:
        # Offload extraction to a thread
        phoneNumbersFromJS = await asyncio.to_thread(
            extractPhoneProcessor.extract_phone_from_file, organised_output_file_path
        )
        standardPhoneNumbers = standardizePhone.updateTheListOfNumbers(phoneNumbersFromJS)
        
        # Offload the parallel phone number validation
        verifiedPhoneNumbers = await asyncio.to_thread(
            validatePhone.validate_phone_numbers_parallel, standardPhoneNumbers
        )
        
        falseNumberInOriginalFormat = getFalseNumbers.get_invalid_phone_numbers(
            phoneNumbersFromJS, verifiedPhoneNumbers
        )
        
        # Offload the phone replacement logic as well
        await asyncio.to_thread(
            replaceWrongPhoneNumbers.replaceNumber, organised_output_file_path, falseNumberInOriginalFormat
        )
    except Exception as e:
        print(f"Error during phone number validation: {e}")


async def validate_address(organised_output_file_path):
    try:
        corrected_address_dict = extractAddress.process_addresses_from_blob(organised_output_file_path)
        replaceCorrectAddress.replaceWithCorrectAddress(organised_output_file_path, corrected_address_dict)
    except Exception as e:
         print(f"Error during address validation: {e}")