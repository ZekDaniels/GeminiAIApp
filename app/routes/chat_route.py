from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat_service import ChatService
from app.db.session import get_db
from app.schemas.chat_schemas import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"],
)

# Initialize services
chat_service = ChatService()

@router.post("/chat_with_pdf", response_model=ChatResponse, status_code=200)
async def chat_with_pdf(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a response based on the user's query and the content of a specified PDF.
    """
    response_text = await chat_service.generate_response(
        integration_id=request.integration_id,
        user_query=request.query,
        db=db,
        only_text=False
    )
    return ChatResponse(response=response_text)


@router.post("/chat_normal", response_model=ChatResponse, status_code=200)
async def chat_normal(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a response based on the user's query without including PDF content.
    """
    response_text = await chat_service.generate_response(
        integration_id=request.integration_id,
        user_query=request.query,
        db=db,
        only_text=True
    )
    return ChatResponse(response=response_text)
