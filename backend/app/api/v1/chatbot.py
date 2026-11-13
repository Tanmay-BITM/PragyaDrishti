from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.services.ai_service import AIService

chatbot_router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])

class ChatbotRequest(BaseModel):
    prompt: Optional[str] = None
    message: Optional[str] = None
    dataset_id: Optional[int] = None

@chatbot_router.post("/ask")
def ask_chatbot(
    req: Optional[ChatbotRequest] = None,
    prompt: Optional[str] = None,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query_text = (req.prompt or req.message) if req else (prompt or "")
    ds_id = req.dataset_id if req and req.dataset_id is not None else dataset_id
    if not query_text:
        raise HTTPException(status_code=400, detail="Prompt parameter is required.")
    return AIService.ask_data_scientist(query_text, ds_id, db)
