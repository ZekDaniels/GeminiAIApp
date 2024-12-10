# app/schemas/chat_schemas.py

from pydantic import BaseModel

class ChatRequest(BaseModel):
    integration_id: int
    query: str

class ChatResponse(BaseModel):
    response: str
