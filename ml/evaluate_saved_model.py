import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
ARTIFACTS = ROOT / "backend" / "model_artifacts"

model_path = ARTIFACTS / "plant_disease_model.keras"
labels_path = ARTIFACTS / "class_names.json"

if not model_path.exists() or not labels_path.exists():
    raise SystemExit("Model or class-label file not found.")

with open(labels_path, encoding="utf-8") as f:
    class_names = json.load(f)

if not (DATA / "test").is_dir():
    raise SystemExit("dataset/test folder not found.")

image_size = (224, 224)
batch_size = 32

test = tf.keras.utils.image_dataset_from_directory(
    DATA / "test",
    image_size=image_size,
    batch_size=batch_size,
    label_mode="int",
    shuffle=False,
)

if test.class_names != class_names:
    raise SystemExit(
        "Test folder class order differs from model labels. "
        "Stopping to prevent misleading metrics."
    )

test = test.map(
    lambda images, labels: (tf.cast(images, tf.float32), labels),
    num_parallel_calls=tf.data.AUTOTUNE,
).prefetch(tf.data.AUTOTUNE)

model = tf.keras.models.load_model(model_path)
loss, accuracy = model.evaluate(test, verbose=1)

true_labels = np.concatenate([y.numpy() for _, y in test])
probabilities = model.predict(test, verbose=1)
predicted_labels = np.argmax(probabilities, axis=1)

report = classification_report(
    true_labels,
    predicted_labels,
    target_names=class_names,
    output_dict=True,
    zero_division=0,
)
matrix = confusion_matrix(
    true_labels, predicted_labels, labels=list(range(len(class_names)))
)

(ARTIFACTS / "saved_model_test_report.json").write_text(
    json.dumps({
        "test_loss": float(loss),
        "test_accuracy": float(accuracy),
        "number_of_test_images": int(len(true_labels)),
        "per_class_report": report,
        "note": "Evaluation of saved checkpoint on held-out PlantVillage test split; not Maharashtra field validation."
    }, indent=2),
    encoding="utf-8",
)
np.savetxt(
    ARTIFACTS / "saved_model_confusion_matrix.csv",
    matrix, delimiter=",", fmt="%d"
)

print(f"\nTest accuracy: {accuracy:.4%}")
print(f"Test loss: {loss:.4f}")
print(f"Report: {ARTIFACTS / 'saved_model_test_report.json'}")
print(f"Confusion matrix: {ARTIFACTS / 'saved_model_confusion_matrix.csv'}")
