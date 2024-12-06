import requests
from app.core.config import settings

def get_gemini_response(pdf_content, query):
    headers = {"Authorization": f"Bearer {settings.gemini_api_key}"}
    payload = {"content": pdf_content, "query": query}
    response = requests.post("https://api.gemini.example.com/query", json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception("Gemini API error")
    return response.json()
