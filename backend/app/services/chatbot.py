import json
import logging
import time
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "diseases.json"


def _load_diseases():
    try:
        with DATA_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not load the plant disease knowledge file")
        return {}


diseases = _load_diseases()


def get_disease_info(user_input: str):
    question = user_input.casefold()
    for disease, info in diseases.items():
        if disease.casefold() in question:
            return disease, info
    return None, None


def ask_plantcare_ai(user_input: str, language: str = "en", history: list | None = None) -> str:
    question = user_input.strip()
    if not question:
        return "Please enter a question about plants or agriculture."

    normalized = ' '.join(question.casefold().strip(' .,!?।').split())
    if normalized in {'hi', 'hii', 'hiii', 'hello', 'hey', 'namaste', 'नमस्ते', 'नमस्कार'}:
        return {'hi': 'नमस्ते! 🌱 मैं PlantCare AI हूँ। फसल, मिट्टी और पौधों की सेहत के बारे में पूछें।', 'mr': 'नमस्कार! 🌱 मी PlantCare AI आहे. पिके, माती आणि वनस्पतींच्या आरोग्याबद्दल विचारा.'}.get(language, 'Namaste! 🌱 I am PlantCare AI. Ask me about crops, soil or plant health.')
    # Keep the quick, curated responses from Siddhi's original chatbot.
    hardcoded = {
        "hi": "Hello! 🌱 I am PlantCare AI. How can I help you with your plants today?",
        "hello": "Hello! 🌿 I'm PlantCare AI. Ask me about plant health, diseases, fertilizers, gardening, or agriculture.",
        "hey": "Hi! 🌱 How can I assist you with your plants today?",
        "bye": "Goodbye! 🌿 Happy gardening!",
        "thank you": "You're welcome! 🌱 Happy to help.",
        "thanks": "You're welcome! 🌱",
        "is buttermilk good for my tomato plant": "Buttermilk is not a reliable fertilizer or disease treatment. Avoid applying it directly to plant leaves or soil; use a balanced compost and fertilizer plan instead.",
        "can i use tea powder for plants": "Used tea leaves can be added to compost. Avoid putting fresh tea powder directly into soil in large amounts.",
        "can i use eggshells for plants": "Crushed eggshells break down slowly and may add calcium over time. Composting them first is a practical option.",
        "can i use banana peel for plants": "Banana peels can be composted, but they are not a complete fertilizer. Use mature compost and soil-test-guided nutrients for crop needs.",
        "how often should i water my tomato plant": "Water according to soil moisture and weather. Keep the root zone evenly moist, avoid waterlogging, and water near the soil rather than wetting leaves.",
        "how much should i water plants in summer": "Check soil moisture regularly and water during cooler hours. Mulch can reduce evaporation; avoid waterlogging.",
        "how much should i water plants in rainy season": "Reduce irrigation when rainfall is sufficient and ensure drainage so roots do not remain waterlogged.",
        "how do i protect plants during heavy rain": "Ensure field drainage, clear blocked channels, and support plants that may lodge. Avoid entering flooded fields.",
        "how do i protect plants from heat": "Use suitable mulch, maintain soil moisture, and provide temporary shade for sensitive nursery plants where practical.",
    }
    if question.casefold() in hardcoded:
        return hardcoded[question.casefold()]

    unrelated_keywords = [
        "virat kohli", "obama", "cricket", "football", "movie", "actor",
        "actress", "song", "music", "ipl", "president", "prime minister",
        "netflix", "youtube", "instagram", "facebook",
    ]
    if any(word in question.casefold() for word in unrelated_keywords):
        return (
            "I'm PlantCare AI 🌱. I focus on plants, crop health, diseases, "
            "fertilizers, gardening, and agriculture. Please ask me something in that area."
        )

    api_key = settings.gemini_api_key.strip()
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured on the backend")
        return "PlantCare AI is not configured yet. Please contact the TreeRasa administrator."

    disease_name, disease_info = get_disease_info(question)
    disease_context = ""
    if disease_info:
        disease_context = f"""
Relevant information from the TreeRasa disease reference:
Disease: {disease_name}
Symptoms: {', '.join(disease_info.get('symptoms', []))}
Cause: {disease_info.get('cause', 'Not specified')}
Treatment: {', '.join(disease_info.get('treatment', []))}
Fertilizer: {disease_info.get('fertilizer', 'Not specified')}
Prevention: {', '.join(disease_info.get('prevention', []))}
"""

    language_name = {"en": "English", "hi": "Hindi (हिन्दी)", "mr": "Marathi (मराठी)"}.get(language, "English")
    history_text = "\\n".join(
        "{}: {}".format("User" if item.get("role") == "user" else "PlantCare AI", str(item.get("content", ""))[:1800])
        for item in (history or [])[-8:]
    )
    prompt = f"""
You are PlantCare AI, the agriculture and plant-care assistant inside TreeRasa.
Always answer in {language_name}, using clear, simple language for farmers and home gardeners in India.
Use this recent conversation as context when relevant:
{history_text}
Focus on crop cultivation, soil, irrigation, plant diseases, pests, fertilizers,
gardening, and how to use TreeRasa. Politely redirect unrelated questions.
Do not invent live weather, market prices, pesticide approvals, or user account data.
For disease diagnosis, explain that text-only advice is preliminary and ask for
crop, location, symptoms, and duration when needed. Recommend local agricultural
experts or KVKs for severe or spreading problems. Give safe, label-following
guidance; do not recommend mixing chemicals.
Keep the answer practical, structured, and concise.
{disease_context}
User question: {question}
"""

    try:
        client = genai.Client(api_key=api_key)
        model = settings.gemini_model.strip() or "gemini-2.5-flash"
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.4),
                )
                answer = getattr(response, "text", None)
                if answer and answer.strip():
                    return answer.strip()
                logger.warning("Gemini returned an empty chatbot response")
                return "I couldn't prepare an answer just now. Please try rephrasing your question."
            except Exception as exc:
                message = str(exc)
                is_temporary = any(code in message for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
                if is_temporary and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                logger.exception("PlantCare AI Gemini request failed")
                return "Sorry, PlantCare AI is temporarily unavailable. Please try again shortly."
    except Exception:
        logger.exception("Could not initialize the Gemini client")
        return "PlantCare AI is temporarily unavailable. Please try again shortly."
