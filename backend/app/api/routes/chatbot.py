from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chatbot import ask_plantcare_ai

router = APIRouter()


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1800)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1800)
    language: Literal["en", "hi", "mr"] = "en"
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=8)


@router.post("/chatbot")
def chatbot(request: ChatRequest):
    answer = ask_plantcare_ai(
        request.message,
        language=request.language,
        history=[item.model_dump() for item in request.history],
    )
    if not answer:
        raise HTTPException(status_code=502, detail="PlantCare AI could not prepare an answer.")
    return {"response": answer}
