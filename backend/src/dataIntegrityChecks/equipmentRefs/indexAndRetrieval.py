# from rank_bm25 import BM25Okapi
# from nltk.tokenize import word_tokenize

# # Tokenize the extracted text
# tokenized_corpus = [word_tokenize(pdf_text.lower())]

# # Build BM25 Index
# bm25 = BM25Okapi(tokenized_corpus)

# # Function to search for a bank name
# def retrieve_relevant_text(query, corpus, bm25):
#     tokenized_query = word_tokenize(query.lower())
#     scores = bm25.get_scores(tokenized_query)
#     highest_score_index = scores.argmax()
#     return corpus[highest_score_index], scores[highest_score_index]

# # Example query
# bank_query = "JP Morgan Chase"
# relevant_text, score = retrieve_relevant_text(bank_query, tokenized_corpus, bm25)
# print(relevant_text, score)
