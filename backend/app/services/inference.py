
"""TreeRasa crop disease prediction and management recommendations."""

import json
import logging
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "model_artifacts"

MODEL_FILES = {
    "plantvillage": ("plant_disease_model_plantvillage.keras", "class_indices_plantvillage.json"),
    "pomegranate": ("plant_disease_model_pomegranate.keras", "class_indices_pomegranate.json"),
    "sugarcane": ("plant_disease_model_sugarcane.keras", "class_indices_sugarcane.json"),
    "cotton": ("plant_disease_model_cotton.keras", "class_indices_cotton.json"),
    "wheat": ("plant_disease_model_wheat.keras", "class_indices_wheat.json"),
}

CROP_ALIASES = {
    "anar": "pomegranate",
    "pomegranate": "pomegranate",
    "sugar cane": "sugarcane",
    "sugarcane": "sugarcane",
    "cotton": "cotton",
    "wheat": "wheat",
    "plantvillage": "plantvillage",
    "other / plantvillage": "plantvillage",
}

# Guidance is matched against the model's exact predicted label.
# Unknown labels receive general, cautious advice rather than a guessed treatment.
RECOMMENDATIONS = {
    "pomegranate": {
        "Healthy": "Maintain orchard sanitation and use well-decomposed compost. Choose fertilizer according to soil testing and the tree's growth stage.",
        "Colletotrichum spp": "This label may indicate a fungal disease. Remove affected plant material where appropriate and seek local agricultural advice. Fertilizer alone will not cure infection.",
        "Ectomylois ceratoniae": "This label may refer to a fruit-boring pest. Inspect fruits and seek local agricultural guidance on pest management and orchard sanitation.",
        "Sunburn": "Maintain appropriate irrigation and canopy protection. Fertilizer is not a direct cure for sunburn.",
        "default": "Confirm the disease or pest identification with a local horticulture expert. Use soil-test-based fertilizer and crop-specific management advice.",
    },
    "sugarcane": {
        "Healthy": "Use soil-test-based fertilizer recommendations. Apply nitrogen in split doses and maintain adequate potassium according to local agricultural guidance.",
        "RedRot": "Use healthy, disease-free planting material and seek local agricultural guidance on infected clumps and field sanitation. Fertilizer does not cure red rot.",
        "Mosaic": "Seek advice on confirming mosaic symptoms, infected plants and vector management. Fertilizer does not cure a viral infection.",
        "Rust": "Confirm the diagnosis with an agricultural expert and follow locally approved disease-management guidance.",
        "Yellow": "This label is ambiguous. Confirm the specific disease or nutrient issue before changing fertilizer application.",
        "default": "Confirm the predicted label with a sugarcane specialist. Use soil-test-based nutrient management and locally approved disease-control guidance.",
    },
    "cotton": {
        "Healthy": "Use soil-test-based fertilizer recommendations. Split nitrogen applications according to crop stage and local agricultural guidance.",
        "Bacterial Blight": "Use recommended resistant varieties and seek local agricultural advice on disease management. Fertilizer is not a cure for bacterial infection.",
        "Aphids": "Inspect the crop and confirm the pest. Encourage beneficial insects and seek local advice before using an approved pest-control product.",
        "default": "Confirm the predicted cotton disease or pest with an agricultural expert before choosing treatment or fertilizer.",
    },
    "wheat": {
        "Healthy": "Apply fertilizer based on soil testing and local wheat recommendations, considering crop stage and irrigation.",
        "Yellow Rust": "Confirm rust symptoms with an agricultural expert and follow locally approved management guidance.",
        "Loose Smut": "Use certified, disease-free seed and seek local guidance on appropriate seed treatment for the next sowing.",
        "default": "Confirm the wheat disease identification before treatment. Use soil-test-based fertilizer recommendations and locally approved disease management.",
    },
    "plantvillage": {
        "default": "Identify the crop and confirm the predicted disease before choosing treatment. Soil testing and crop-specific agricultural advice can guide fertilizer application.",
    },
}


def choose_model(crop_name: str | None) -> str:
    if not crop_name or not crop_name.strip():
        return "plantvillage"
    return CROP_ALIASES.get(crop_name.strip().lower(), "plantvillage")


def read_labels(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        labels = data
    elif isinstance(data, dict):
        # Expected format: {"class label": 0, "another label": 1}
        if all(str(value).isdigit() for value in data.values()):
            labels = [
                label for label, index in
                sorted(data.items(), key=lambda item: int(item[1]))
            ]
        # Also support {"0": "class label", "1": "another label"}.
        elif all(str(key).isdigit() for key in data.keys()):
            labels = [
                label for index, label in
                sorted(data.items(), key=lambda item: int(item[0]))
            ]
        else:
            raise ValueError(f"Unsupported label mapping in {path.name}")
    else:
        raise ValueError(f"Invalid labels file: {path.name}")

    if not labels or not all(isinstance(label, str) for label in labels):
        raise ValueError(f"Invalid class labels in {path.name}")
    return labels


@lru_cache(maxsize=5)
def load_model(model_key: str):
    import tensorflow as tf

    if model_key not in MODEL_FILES:
        raise ValueError(f"Unsupported crop model: {model_key}")

    model_file, labels_file = MODEL_FILES[model_key]
    model_path = ARTIFACT_DIR / model_file
    labels_path = ARTIFACT_DIR / labels_file

    if not model_path.is_file() or not labels_path.is_file():
        raise FileNotFoundError(f"Missing model or labels for {model_key}")

    labels = read_labels(labels_path)
    model = tf.keras.models.load_model(model_path, compile=False)
    output_units = int(model.output_shape[-1])

    if output_units < 2 or output_units != len(labels):
        raise ValueError(
            f"{model_key}: model outputs {output_units} classes but "
            f"{len(labels)} labels were found. Check the model and labels."
        )

    return model, labels


def predict_plant(
    image_bytes: bytes,
    filename: str | None = None,
    crop_name: str | None = None,
) -> dict:
    model_key = choose_model(crop_name)

    try:
        model, labels = load_model(model_key)

        with Image.open(BytesIO(image_bytes)) as image:
            image_array = np.asarray(
                image.convert("RGB").resize((224, 224)),
                dtype=np.float32,
            )

        # Keep preprocessing consistent with training. This uses raw 0–255
        # pixels, matching a training pipeline that did not rescale inputs.
        probabilities = model.predict(
            np.expand_dims(image_array, axis=0),
            verbose=0,
        )[0]

        best_index = int(np.argmax(probabilities))
        confidence = float(probabilities[best_index])
        predicted_label = labels[best_index]

        advice = RECOMMENDATIONS.get(
            model_key, RECOMMENDATIONS["plantvillage"]
        )
        recommendation = advice.get(
            predicted_label,
            advice.get(
                "default",
                "Confirm the prediction with an agricultural expert before treatment.",
            ),
        )

        if confidence < 0.55:
            return {
                "status": "low_confidence",
                "predicted_disease": "Uncertain prediction",
                "crop_name": model_key,
                "confidence": round(confidence, 4),
                "recommendations": (
                    "The model is uncertain. Try a clear, well-lit photo "
                    "of one leaf. Do not choose treatment or fertilizer "
                    "based on this prediction alone."
                ),
            }

        return {
            "status": "success",
            "predicted_disease": predicted_label,
            "crop_name": model_key,
            "confidence": round(confidence, 4),
            "recommendations": (
                f"Fertilizer and management guidance:\n{recommendation}\n\n"
                "This is an AI prediction, not a confirmed diagnosis. "
                "Consult a local agricultural expert before choosing treatment."
            ),
        }

    except Exception as exc:
        logger.exception("Plant prediction failed for %s", filename or "upload")
        return {
            "status": "inference_error",
            "predicted_disease": "Prediction failed",
            "crop_name": model_key,
            "confidence": None,
            "recommendations": (
                f"Prediction could not be completed ({type(exc).__name__}). "
                "Check the backend terminal for details."
            ),
        }
