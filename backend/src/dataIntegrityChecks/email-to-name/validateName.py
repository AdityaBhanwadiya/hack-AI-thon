import os
from uuid import uuid4
from langchain.chat_models import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

def organize(input_dict: dict):
    # Load environment variables from .env file
    load_dotenv()

    # Set environment variables for Azure OpenAI and LangChain API keys
    os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

    # Langsmith Tracking
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

    # Prompt Template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an AI assistant. Help me with this. The email address is 100% verified, based on that, check if the mail address is made of first name and last name given in key?"
             "If yes, then only check if that is valid or not."
             "Eg.: Tatyana Posibleva: tatyana.pogibleva@gmail.com, over here there is some mistake with the last name according to email, so change the name accordingly. Don't EVER change the email."
             "Eg.: Abid Mohammed: abid_jm@yahoo.com, over here do nothing just say \"Looks Good!\" "
             "Eg.: Royal Caravan: rcco2019@primein.com, over here do nothing just say \"Company Email\" "
            "Only give the output that is asked for, nothing else."
            ),
            ("user", "Text data:\n{text_data}")
        ]
    )

    # Azure OpenAI LLM
    llm = AzureChatOpenAI(
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_GPT4O_DEPLOYMENT_NAME"),
        temperature=0.1
    )
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser

    # Prepare the text data from the dictionary
    input_text = "\n".join([f"{name}: {email}" for name, email in input_dict.items()])

    # Invoke the chain
    response = chain.invoke({'text_data': input_text})

    # Print the response
    print(response)

# Example dictionary input
input_dict = {
    "John Done": "john.doe@example.com",
    "Jane Swith": "jane.smith@company.com",
    "Alice Jobson": "alice.johnson@example.com"
}

organize(input_dict)
