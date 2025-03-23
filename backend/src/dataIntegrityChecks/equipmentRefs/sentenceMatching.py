# from transformers import BertTokenizer, BertForSequenceClassification
# import torch

# # Load pre-trained BERT model and tokenizer
# tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
# model = BertForSequenceClassification.from_pretrained('bert-base-uncased')

# # Function to match the query and retrieved text
# def match_bank_name(query, retrieved_text):
#     inputs = tokenizer.encode_plus(query, retrieved_text, return_tensors='pt', max_length=128, truncation=True)
#     outputs = model(**inputs)
    
#     # Get confidence score (softmax)
#     probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
#     return probs

# # Example usage
# match_score = match_bank_name(bank_query, relevant_text)
# print(f"Match confidence score: {match_score}")
