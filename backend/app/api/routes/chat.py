import json
import time
from collections import defaultdict, deque
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Request as FastAPIRequest
from app.core.config import settings
from pydantic import BaseModel, Field

router = APIRouter(prefix="/chat", tags=["TreeRasa Assistant"])

# Lightweight per-process abuse protection. Use a shared rate limiter (for example Redis)
# if the API is later deployed with multiple workers/instances.
_requests: dict[str, deque[float]] = defaultdict(deque)
WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 12


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1800)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1800)
    language: Literal["en", "hi", "mr"] = "en"
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    reply: str
    language: str


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    events = _requests[ip]
    while events and now - events[0] > WINDOW_SECONDS:
        events.popleft()
    if len(events) >= MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(status_code=429, detail="Too many messages. Please wait a minute and try again.")
    events.append(now)


def _language_name(language: str) -> str:
    return {"en": "English", "hi": "Hindi (हिन्दी)", "mr": "Marathi (मराठी)"}[language]


def _generate_reply(payload: ChatRequest, api_key: str, model: str) -> str:
    language_name = _language_name(payload.language)
    system_instruction = f"""
You are TreeRasa Assistant, a helpful agricultural information guide for farmers,
vendors and customers using the TreeRasa platform in India.

RESPONSE LANGUAGE: Reply naturally and clearly in {language_name}. Keep using this
language unless the user explicitly asks to switch. For Marathi use natural Marathi,
and for Hindi use natural Hindi. Do not answer in English just because technical
terms are commonly written in English; explain them in the selected language.

YOUR SCOPE:
- Crop selection, sowing seasons, seed selection, soil health, irrigation, nutrients,
  compost, common pests and diseases, integrated pest management, harvesting and storage.
- General farming practices relevant to Indian conditions. Ask for the crop, location,
  season and visible symptoms when those details materially affect the advice.
- TreeRasa features: plant-health scans and scan history for farmers/users; fresh-produce
  marketplace; seeds/fertilizers marketplace; product listings for eligible farmers/vendors;
  orders, product reviews/ratings, notifications and profile settings.
- Explain how to use TreeRasa, but do not claim to see a user's private account, order,
  scan, stock or notification data.

ACCURACY AND SAFETY:
- Be practical, concise and respectful. Use numbered steps where helpful.
- Never invent live weather, market prices, stock, seller details, government scheme
  eligibility or current order status. Say when live data is not connected.
- A photo-based or text-based symptom discussion is not a confirmed diagnosis. Explain
  uncertainty and suggest an agricultural officer/KVK or qualified agronomist for
  serious or spreading crop problems.
- Do not recommend mixing pesticides or give unsafe chemical instructions. For any
  pesticide, advise following the exact product label, local regulations, protective
  equipment and guidance from a qualified local agriculture professional.
- If a question is outside farming or TreeRasa, politely say what you can help with.
- Do not claim that you performed actions in the TreeRasa account.
Keep the answer useful for small and medium Indian farms. Use metric units.
"""
    contents = []
    for item in payload.history[-8:]:
        text = item.content.strip()
        if text:
            contents.append({
                "role": "model" if item.role == "assistant" else "user",
                "parts": [{"text": text[:1800]}],
            })
    contents.append({"role": "user", "parts": [{"text": payload.message.strip()}]})

    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.45, "maxOutputTokens": 850},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not return provider response bodies or credentials to public clients.
        if exc.code in (401, 403):
            raise HTTPException(status_code=503, detail="The assistant is not configured correctly yet.") from exc
        if exc.code == 429:
            raise HTTPException(status_code=503, detail="The assistant is busy. Please try again shortly.") from exc
        raise HTTPException(status_code=502, detail="The assistant could not answer right now. Please try again.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="Could not connect to the assistant. Please try again.") from None

    candidates = result.get("candidates") or []
    parts = (candidates[0].get("content") or {}).get("parts") if candidates else []
    reply = "\n".join(part.get("text", "") for part in (parts or []) if part.get("text")).strip()
    if not reply:
        raise HTTPException(status_code=502, detail="The assistant returned an empty answer. Please try again.")
    return reply[:6000]


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, request: FastAPIRequest):
    _check_rate_limit(request.client.host if request.client else "unknown")
    api_key = settings.gemini_api_key.strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="TreeRasa Assistant is not configured yet. The site administrator needs to add GEMINI_API_KEY to the backend environment.",
        )
    model = settings.gemini_model.strip() or "gemini-2.5-flash"
    reply = _generate_reply(payload, api_key, model)
    return ChatResponse(reply=reply, language=payload.language)
