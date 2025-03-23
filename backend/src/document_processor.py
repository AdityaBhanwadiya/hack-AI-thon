from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

class DocumentProcessor:
    def __init__(self, endpoint, api_key):
        self.document_client = DocumentAnalysisClient(
            endpoint=endpoint,  
            credential=AzureKeyCredential(api_key)  
        )
    
    def extract_text_from_document(self, file_path):
        """
        Extracts text from a document using Azure Document Intelligence.
        """
        with open(file_path, "rb") as file:
            poller = self.document_client.begin_analyze_document("prebuilt-read", file) 
            result = poller.result()

        # Extract and return text
        extracted_text = "\n".join([line.content for page in result.pages for line in page.lines])
        return extracted_text
