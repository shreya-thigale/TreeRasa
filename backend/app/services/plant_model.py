"""Load task-specific trained models only when their artifact files exist."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from app.core.config import settings

_cached_bundles: dict[str, tuple] = {}
_cached_signatures: dict[str, tuple[int, int]] = {}


def _artifact_paths(task: str) -> tuple[Path, Path]:
    if task == "pest":
        return settings.backend_path(settings.pest_model_path), settings.backend_path(settings.pest_labels_path)
    return settings.backend_path(settings.model_path), settings.backend_path(settings.labels_path)


def load_model_bundle(task: str = "disease"):
    """Cache the loaded model by task and reload it when files are replaced after training."""
    if task not in {"disease", "pest"}:
        raise ValueError("Model task must be 'disease' or 'pest'.")
    model_path, labels_path = _artifact_paths(task)
    if not model_path.exists() or not labels_path.exists():
        return None
    signature = (model_path.stat().st_mtime_ns, labels_path.stat().st_mtime_ns)
    if task in _cached_bundles and signature == _cached_signatures.get(task):
        return _cached_bundles[task]
    # TensorFlow is optional until an artifact exists, so normal API usage does not require ML dependencies.
    import tensorflow as tf
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(labels, list) or len(labels) < 2:
        raise ValueError(f"The class label file is invalid: {labels_path}")
    bundle = (tf.keras.models.load_model(model_path), labels)
    _cached_bundles[task] = bundle
    _cached_signatures[task] = signature
    return bundle


def predict_image(image_path: Path, task: str = "disease") -> tuple[str, float] | None:
    bundle = load_model_bundle(task)
    if bundle is None:
        return None
    model, labels = bundle
    with Image.open(image_path) as image:
        pixels = np.asarray(image.convert("RGB").resize((224, 224)), dtype=np.float32)
    # MobileNetV2 preprocessing is inside the saved Keras model. Pass raw 0–255 RGB pixels here.
    probabilities = model.predict(np.expand_dims(pixels, axis=0), verbose=0)[0]
    if len(probabilities) != len(labels):
        raise ValueError("Model output count does not match the saved class label file.")
    index = int(np.argmax(probabilities))
    return labels[index], float(probabilities[index])
