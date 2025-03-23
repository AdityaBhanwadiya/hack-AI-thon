# import requests
# from bs4 import BeautifulSoup

# def scrape_company_info(company_name):
#     search_url = f"https://www.google.com/search?q={company_name}+company"
#     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

#     response = requests.get(search_url, headers=headers)
#     soup = BeautifulSoup(response.text, "html.parser")
    
#     # This is an example of finding data from a search result snippet
#     for result in soup.find_all('h3'):
#         if company_name.lower() in result.text.lower():
#             return result.text

#     return "Company not found"

# # Example usage
# company_to_verify = "Beround Inc."
# result = scrape_company_info(company_to_verify)
# print(result)
