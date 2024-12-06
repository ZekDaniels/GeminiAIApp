import requests
from fastapi import HTTPException
from app.core.config import settings


def get_gemini_response(pdf_content, query):
    """
    Query the Gemini API with the PDF content and user query, and return the response.
    """
    try:
        headers = {"Authorization": f"Bearer {settings.gemini_api_key}"}
        payload = {"content": pdf_content, "query": query}
        response = requests.post("https://api.gemini.example.com/query", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception("Gemini API error")

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error with Gemini API: {str(e)}")
