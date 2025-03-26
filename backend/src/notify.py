import requests

def notify_status(message):
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        url="https://azure-hackathon-fa.azurewebsites.net/api/send_message",
        json={"message": message},
        headers=headers
    )
    print("notify_status response:", response.status_code, response.text)