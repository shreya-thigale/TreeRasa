from google import genai
import json
import time
import os
from pathlib import Path


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "diseases.json"

with open(DATA_PATH, "r", encoding="utf-8") as file:
    diseases = json.load(file)


def get_disease_info(user_input):
    for disease in diseases:
        if disease.lower() in user_input.lower():
            return disease, diseases[disease]

    return None, None


def ask_plantcare_ai(user_input):

    question = user_input.lower().strip()

    # -----------------------------
    # Hardcoded Responses
    # -----------------------------
    hardcoded = {

        # Greetings
        "hi": "Hello! 🌱 I am PlantCare AI. How can I help you with your plants today?",
        "hello": "Hello! 🌿 I'm PlantCare AI. Ask me anything about plant health, diseases, fertilizers, or gardening.",
        "hey": "Hi! 🌱 How can I assist you with your plants today?",
        "bye": "Goodbye! 🌿 Happy Gardening!",
        "thank you": "You're welcome! 🌱 Happy to help.",
        "thanks": "You're welcome! 🌱",

        # Home gardening
        "is buttermilk good for my tomato plant": (
            "Yes, buttermilk can help in small quantities because it contains beneficial microbes. Avoid using it frequently, as excessive application may attract insects or create fungal growth."
        ),

        "can i use tea powder for plants": (
            "Used tea leaves can be added to compost. Avoid putting fresh tea powder directly into the soil in large amounts."
        ),

        "can i use eggshells for plants": (
            "Yes. Crushed eggshells slowly add calcium to the soil and can improve soil quality."
        ),

        "can i use banana peel for plants": (
            "Yes. Banana peels are rich in potassium. Compost them before use for the best results."
        ),

        "how often should i water my tomato plant": (
            "Water deeply when the top 2–3 cm of soil feels dry. Avoid overwatering."
        ),

        # Weather
        "how much should i water plants in summer": (
            "During summer, water early in the morning or evening. Increase watering based on soil moisture, but avoid waterlogging."
        ),

        "how much should i water plants in rainy season": (
            "Reduce watering during the rainy season. Water only if the soil feels dry to avoid root rot."
        ),

        "how do i protect plants during heavy rain": (
            "Ensure proper drainage, remove standing water, and provide temporary covers for delicate plants."
        ),

        "how do i protect plants from heat": (
            "Water during cooler hours, apply mulch, and provide partial shade during extreme heat."
        ),
    }

    if question in hardcoded:
        return hardcoded[question]

    # ------------------------------------
    # Reject unrelated questions instantly
    # ------------------------------------
    unrelated_keywords = [
        "virat kohli",
        "obama",
        "cricket",
        "football",
        "movie",
        "actor",
        "actress",
        "song",
        "music",
        "ipl",
        "president",
        "prime minister",
        "netflix",
        "youtube",
        "instagram",
        "facebook",
    ]

    if any(word in question for word in unrelated_keywords):
        return (
            "I'm PlantCare AI 🌱. I can only answer questions related to plants, "
            "plant diseases, fertilizers, gardening, and agriculture."
        )

    # Search disease database
    disease_name, disease_info = get_disease_info(user_input)

    if disease_info:

        context = f"""
You are PlantCare AI.

Answer only plant-related questions.

Disease:
{disease_name}

Symptoms:
{', '.join(disease_info['symptoms'])}

Cause:
{disease_info['cause']}

Treatment:
{', '.join(disease_info['treatment'])}

Fertilizer:
{disease_info['fertilizer']}

Prevention:
{', '.join(disease_info['prevention'])}

Explain in simple language.

User:
{user_input}
"""

    else:

        context = f"""
You are PlantCare AI.

Rules:
- Answer only plant related questions.
- Politely refuse unrelated questions.
- Give simple answers.
- Do not make false claims.

Question:
{user_input}
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=context
            )

            return response.text

        except Exception as e:

            if "503" in str(e) and attempt < 2:

                time.sleep(5)

            else:
                return (
    "Sorry, PlantCare AI is temporarily busy. "
    "Please try again in a few moments."
)
            



            