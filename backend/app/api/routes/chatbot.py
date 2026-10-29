from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chatbot import ask_plantcare_ai


router = APIRouter()


class ChatRequest(BaseModel):
    message: str



@router.post("/chatbot")
def chatbot(request: ChatRequest):

    print("Chatbot request received:", request.message)

    answer = ask_plantcare_ai(request.message)

    print("Gemini response received")

    return {
        "response": answer
    }