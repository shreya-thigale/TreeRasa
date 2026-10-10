"""Train and evaluate a plant-image classifier using transfer learning.

The held-out test split is used only once for final evaluation. Model and label artifacts
are written to the directory the API expects by default: backend/model_artifacts/.
Run this script from the repository root after preparing a labelled dataset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

IMAGE_SIZE = (224, 224)
DEFAULT_BATCH_SIZE = 32
DEFAULT_SEED = 42
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def load_split(data_root: Path, split_name: str, batch_size: int, seed: int):
    split_path = data_root / split_name
    if not split_path.is_dir():
        raise SystemExit(f"Missing {split_path}. Run prepare_dataset.py first.")
    return tf.keras.utils.image_dataset_from_directory(
        split_path,
        image_size=IMAGE_SIZE,
        batch_size=batch_size,
        label_mode="int",
        shuffle=(split_name == "train"),
        seed=seed,
    )


def count_class_images(split_path: Path, class_name: str) -> int:
    return sum(1 for path in (split_path / class_name).rglob("*")
               if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def build_model(class_count: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    """Build a MobileNetV2 classifier; return both the complete and backbone models."""
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.06),
            tf.keras.layers.RandomZoom(0.08),
            tf.keras.layers.RandomContrast(0.08),
        ],
        name="training_augmentation",
    )
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(*IMAGE_SIZE, 3), include_top=False, weights="imagenet"
    )
    backbone.trainable = False

    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3), name="plant_image_rgb")
    images = augmentation(inputs)
    # Preprocessing is saved inside the model, so the API must supply 0..255 RGB pixels.
    images = tf.keras.applications.mobilenet_v2.preprocess_input(images)
    features = backbone(images, training=False)
    features = tf.keras.layers.GlobalAveragePooling2D()(features)
    features = tf.keras.layers.Dropout(0.30)(features)
    outputs = tf.keras.layers.Dense(class_count, activation="softmax", name="class_probabilities")(features)
    model = tf.keras.Model(inputs, outputs, name="treerasa_plant_classifier")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, backbone


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="dataset", help="Folder containing train/, val/ and test/")
    parser.add_argument("--output-dir", default="backend/model_artifacts", help="Where model and evaluation files are saved")
    parser.add_argument("--model-name", default="plant_disease_model", help="Artifact filename stem")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--fine-tune-epochs", type=int, default=0, help="Optional final-backbone fine tuning")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.epochs < 1 or args.fine_tune_epochs < 0 or args.batch_size < 1:
        raise SystemExit("Epochs and batch size must be positive; fine-tuning epochs cannot be negative.")

    tf.keras.utils.set_random_seed(args.seed)
    data_root = Path(args.data_root)
    train = load_split(data_root, "train", args.batch_size, args.seed)
    validation = load_split(data_root, "val", args.batch_size, args.seed)
    test = load_split(data_root, "test", args.batch_size, args.seed)
    class_names = train.class_names
    if len(class_names) < 2:
        raise SystemExit("At least two classes are required.")
    for split_name, dataset in (("val", validation), ("test", test)):
        if dataset.class_names != class_names:
            raise SystemExit(f"Class folders or order differ in {split_name}. Every split must use the same class folders.")

    train_counts = np.asarray([count_class_images(data_root / "train", name) for name in class_names], dtype=np.int64)
    if np.any(train_counts == 0):
        raise SystemExit("Every class must contain at least one training image.")
    class_weights = compute_class_weight(
        class_weight="balanced", classes=np.arange(len(class_names)),
        y=np.concatenate([np.full(int(count), index, dtype=np.int64) for index, count in enumerate(train_counts)]),
    )
    class_weight_map = {index: float(weight) for index, weight in enumerate(class_weights)}
    auto_tune = tf.data.AUTOTUNE
    train = train.shuffle(1000, seed=args.seed, reshuffle_each_iteration=True).prefetch(auto_tune)
    validation = validation.prefetch(auto_tune)
    test = test.prefetch(auto_tune)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{args.model_name}.keras"
    labels_path = output_dir / ("class_names.json" if args.model_name == "plant_disease_model" else f"{args.model_name}_class_names.json")
    history_path = output_dir / f"{args.model_name}_training_history.csv"
    (output_dir / "dataset_counts.json").write_text(
        json.dumps({name: int(train_counts[index]) for index, name in enumerate(class_names)}, indent=2),
        encoding="utf-8",
    )
    labels_path.write_text(json.dumps(class_names, indent=2), encoding="utf-8")

    model, backbone = build_model(len(class_names))
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(str(model_path), monitor="val_loss", save_best_only=True, verbose=1),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=2, min_lr=1e-6, verbose=1),
        tf.keras.callbacks.CSVLogger(str(history_path)),
    ]
    print("\nClass order used by the model:")
    for index, class_name in enumerate(class_names):
        print(f"  {index}: {class_name} ({train_counts[index]} training images)")
    print("\nTraining classifier head. Validation data selects checkpoints; test data remains untouched.")
    model.fit(train, validation_data=validation, epochs=args.epochs, callbacks=callbacks, class_weight=class_weight_map)

    if args.fine_tune_epochs:
        print("\nFine-tuning the final 30 backbone layers with a lower learning rate.")
        backbone.trainable = True
        for layer in backbone.layers[:-30]:
            layer.trainable = False
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                      loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        model.fit(train, validation_data=validation, epochs=args.fine_tune_epochs,
                  callbacks=callbacks, class_weight=class_weight_map)

    # Restore the best checkpoint selected only by validation loss before final testing.
    model = tf.keras.models.load_model(model_path)
    test_loss, test_accuracy = model.evaluate(test, verbose=1)
    true_labels = np.concatenate([labels.numpy() for _, labels in test], axis=0)
    probabilities = model.predict(test, verbose=1)
    predicted_labels = np.argmax(probabilities, axis=1)
    report_text = classification_report(true_labels, predicted_labels, target_names=class_names, zero_division=0)
    report_json = classification_report(true_labels, predicted_labels, target_names=class_names,
                                        output_dict=True, zero_division=0)
    matrix = confusion_matrix(true_labels, predicted_labels, labels=list(range(len(class_names))))
    (output_dir / f"{args.model_name}_test_report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")
    (output_dir / f"{args.model_name}_test_report.txt").write_text(report_text, encoding="utf-8")
    np.savetxt(output_dir / f"{args.model_name}_confusion_matrix.csv", matrix, delimiter=",", fmt="%d")

    figure_size = (max(9, len(class_names) * 0.45), max(7, len(class_names) * 0.40))
    plt.figure(figsize=figure_size)
    plt.imshow(matrix, interpolation="nearest", cmap="Blues")
    plt.title(f"TreeRasa — {args.model_name} held-out test confusion matrix")
    plt.colorbar()
    ticks = np.arange(len(class_names))
    plt.xticks(ticks, class_names, rotation=90)
    plt.yticks(ticks, class_names)
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(output_dir / f"{args.model_name}_confusion_matrix.png", dpi=160)
    plt.close()

    summary = {
        "model": "MobileNetV2 transfer learning",
        "artifact": model_path.name,
        "classes": class_names,
        "image_size": list(IMAGE_SIZE),
        "test_loss": float(test_loss),
        "test_accuracy": float(test_accuracy),
        "seed": args.seed,
        "test_split": "held-out test directory; not used for training or checkpoint selection",
        "warning": "A benchmark score does not establish field accuracy. Test on independent farms, phones, seasons and lighting before deployment.",
    }
    (output_dir / f"{args.model_name}_evaluation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nHELD-OUT TEST RESULTS (not training accuracy)")
    print(json.dumps(summary, indent=2))
    print(f"\nModel saved to: {model_path.resolve()}")
    print(f"Labels saved to: {labels_path.resolve()}")
    print("Review per-class precision/recall/F1 and the confusion matrix, not accuracy alone.")


if __name__ == "__main__":
    main()
