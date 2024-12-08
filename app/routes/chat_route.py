from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.chat_service import ChatService
from app.db.session import get_db
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.errors.pdf_exceptions import PDFNotFoundException

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"],
)

chat_service = ChatService()

@router.post("/chat_with_pdf", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Generate a response based on the user's query and the content of a specified PDF.

    Args:
        request (ChatRequest): The user's query and the PDF ID.
        db (Session): The database session dependency.

    Returns:
        ChatResponse: The generated response.

    Raises:
        HTTPException: If an error occurs during response generation.
    """
    try:
        response_text = chat_service.generate_response(
            pdf_id=request.pdf_id,
            user_query=request.query,
            db=db
        )
        return ChatResponse(response=response_text)
    except PDFNotFoundException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")


@router.post("/chat_normal", response_model=ChatResponse)
async def chat_normal(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Generate a response based on the user's query and the content of a specified PDF.

    Args:
        request (ChatRequest): The user's query and the PDF ID.
        db (Session): The database session dependency.

    Returns:
        ChatResponse: The generated response.

    Raises:
        HTTPException: If an error occurs during response generation.
    """
    try:
        response_text = chat_service.generate_response(
            pdf_id=request.pdf_id,
            user_query=request.query,
            db=db,
            only_text=True
        )
        return ChatResponse(response=response_text)
    except PDFNotFoundException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")