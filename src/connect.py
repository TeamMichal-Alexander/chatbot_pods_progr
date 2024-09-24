import requests
from requests import RequestException


def ask_ollama_server(prompt, model):
    api_url = "http://localhost:9999/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "model": model,
        "stream": False
    }
    response = send_api_request(api_url, headers=headers, data=data)

    return response


def send_api_request(api_url, headers=None, data=None):
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Bląd: {e}")
        return None