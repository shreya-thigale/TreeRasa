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
    # Curated answers for common farmer questions. These work without Gemini.
    curated = {
        "soil": {
            "en": "To improve soil health: (1) add well-decomposed compost or farmyard manure, (2) grow legumes or use suitable cover crops in rotation, (3) keep soil covered with mulch or crop residue, (4) avoid working soil when it is too wet, and (5) base fertilizer use on a soil test. What crop and soil type do you have?",
            "hi": "मिट्टी की सेहत सुधारने के लिए: (1) अच्छी तरह सड़ी हुई कम्पोस्ट या गोबर की खाद डालें, (2) फसल चक्र में दलहनी फसलें शामिल करें, (3) मल्च या फसल अवशेष से मिट्टी ढकें, (4) बहुत गीली मिट्टी में जुताई न करें और (5) मिट्टी की जाँच के आधार पर खाद डालें। आपकी फसल और मिट्टी का प्रकार क्या है?",
            "mr": "मातीची सुपीकता सुधारण्यासाठी: (1) पूर्ण कुजलेले कंपोस्ट किंवा शेणखत वापरा, (2) पीक फेरपालटीत कडधान्य पिकांचा समावेश करा, (3) आच्छादन किंवा पिकांचे अवशेष वापरून माती झाका, (4) अत ओली माती नांगरू नका आणि (5) माती परीक्षणानुसार खत द्या. तुमचे पीक आणि मातीचा प्रकार कोणता आहे?"
        },
        "yellow": {
            "en": "Yellow leaves can be caused by overwatering, poor drainage, nutrient deficiency, pests or disease. Check soil moisture and the underside of leaves. Tell me the crop, whether older or newer leaves are yellow, and how long this has been happening.",
            "hi": "पत्तों का पीला होना अधिक पानी, खराब जल निकास, पोषक तत्वों की कमी, कीट या रोग के कारण हो सकता है। मिट्टी की नमी और पत्तों के नीचे की जाँच करें। फसल का नाम बताएं और यह भी कि पुराने पत्ते पीले हैं या नए।",
            "mr": "पाने पिवळी होण्यामागे जास्त पाणी, खराब निचरा, अन्नद्रव्यांची कमतरता, कीड किंवा रोग कारणीभूत असू शकतात. मातीतील ओलावा आणि पानांची खालची बाजू तपासा. कोणते पीक आहे आणि जुनी की नवी पाने पिवळी होत आहेत ते सांगा."
        },
        "watering": {
            "en": "Water based on soil moisture rather than a fixed schedule. Check the root zone, water slowly near the soil, and avoid waterlogging. Hot weather, soil type and plant stage all affect water needs.",
            "hi": "पानी देने का समय तय कैलेंडर के बजाय मिट्टी की नमी देखकर तय करें। जड़ों के पास की मिट्टी जाँचें, धीरे-धीरे पौधे के आधार पर पानी दें और जलभराव से बचें। गर्मी, मिट्टी और फसल की अवस्था के अनुसार पानी की ज़रूरत बदलती है।",
            "mr": "ठराविक वेळापत्रकाऐवजी मातीतील ओलावा पाहून पाणी द्या. मुळांजवळील माती तपासा, झाडाच्या बुंध्याजवळ हळूहळू पाणी द्या आणि पाणी साचू देऊ नका. उष्णता, मातीचा प्रकार आणि पिकाची अवस्था यानुसार पाण्याची गरज बदलते."
        },
        "compost": {
            "en": "Use mature, well-decomposed compost. Mix it into the soil before planting or apply a modest layer around established plants without piling it against stems. Compost improves soil structure but may not supply every nutrient a crop needs.",
            "hi": "अच्छी तरह तैयार और पूरी तरह सड़ी हुई कम्पोस्ट इस्तेमाल करें। बुवाई से पहले मिट्टी में मिलाएँ या बड़े पौधों के आसपास थोड़ी परत डालें; तने से सटाकर ढेर न लगाएँ। कम्पोस्ट मिट्टी की संरचना सुधारती है, लेकिन हर पोषक तत्व की पूरी ज़रूरत नहीं पूरी करती।",
            "mr": "पूर्ण कुजलेले कंपोस्ट वापरा. लागवडीपूर्वी ते मातीत मिसळा किंवा वाढलेल्या झाडाभोवती थर द्या; खोडाला लागून ढीग करू नका. कंपोस्टमुळे मातीची रचना सुधारते, पण पिकांना लागणारी सर्व अन्नद्रव्ये त्यातून मिळतीलच असे नाही."
        },
        "tomato": {
            "en": "For tomato plants, keep soil evenly moist but not waterlogged. Water at the base in the morning when practical, use mulch to reduce evaporation, and provide support as plants grow. Avoid frequent wetting of foliage.",
            "hi": "टमाटर के पौधों की मिट्टी में समान नमी रखें, लेकिन पानी जमा न होने दें। संभव हो तो सुबह जड़ों के पास पानी दें, नमी बनाए रखने के लिए मल्च इस्तेमाल करें और पौधों को सहारा दें। पत्तों को बार-बार गीला करने से बचें।",
            "mr": "टोमॅटोच्या झाडांच्या मातीत समान ओलावा ठेवा, पण पाणी साचू देऊ नका. शक्य असल्यास सकाळी बुंध्याजवळ पाणी द्या, ओलावा टिकवण्यासाठी आच्छादन वापरा आणि झाडांना आधार द्या. पानांवर वारंवार पाणी पडू देऊ नका."
        }
    }
    faq_phrases = {
        "soil": ["how can i improve soil health", "how to improve soil health", "soil health", "मिट्टी की सेहत कैसे सुधारें", "मिट्टी की उर्वरता कैसे बढ़ाएं", "मातीची सुपीकता कशी वाढवू", "मातीची सुपीकता कशी वाढवावी"],
        "yellow": ["why are my plant leaves turning yellow", "why are leaves yellow", "leaves turning yellow", "पत्ते पीले क्यों हो रहे हैं", "पौधों के पत्ते पीले क्यों होते हैं", "पाने पिवळी का पडतात", "झाडांची पाने पिवळी का होतात"],
        "watering": ["how often should i water plants", "how much should i water plants", "when should i water plants", "पौधों को कितनी बार पानी दें", "पौधों में पानी कब डालें", "झाडांना किती वेळा पाणी द्यावे", "पिकांना पाणी कधी द्यावे"],
        "compost": ["how to use compost", "is compost good for plants", "कम्पोस्ट का उपयोग कैसे करें", "खाद का उपयोग कैसे करें", "कंपोस्ट कसे वापरावे", "कंपोस्ट झाडांसाठी कसे वापरावे"],
        "tomato": ["how to care for tomato plants", "tomato plant care", "टमाटर के पौधे की देखभाल कैसे करें", "टोमॅटोच्या झाडांची काळजी कशी घ्यावी"]
    }
    for topic, phrases in faq_phrases.items():
        if any(phrase in normalized for phrase in phrases):
            return curated[topic].get(language, curated[topic]["en"])

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
