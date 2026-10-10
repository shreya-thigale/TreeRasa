"""Combine selected labelled image folders using an explicit canonical-label map.

Mapping CSV columns: source_root,source_class,canonical_class
Example row: downloads/PlantVillage/PlantVillage,Tomato___Early_blight,tomato_early_blight

Only map labels after checking that the source categories really describe the same condition.
The script does not infer label equivalence or merge unrelated plant/pest tasks.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", default="label_map.csv", help="CSV with source_root, source_class, canonical_class")
    parser.add_argument("--output", default="raw_dataset", help="Canonical class-folder output")
    args = parser.parse_args()
    mapping_path = Path(args.mapping)
    if not mapping_path.is_file():
        raise SystemExit(f"Mapping file not found: {mapping_path}")
    output_root = Path(args.output)
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"Output folder is not empty: {output_root}. Choose a new folder or clear it intentionally.")
    seen: dict[str, str] = {}
    copied = 0
    with mapping_path.open(newline="", encoding="utf-8-sig") as mapping_file:
        rows = list(csv.DictReader(mapping_file))
    required = {"source_root", "source_class", "canonical_class"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit("Mapping CSV needs columns: source_root, source_class, canonical_class")
    for row in rows:
        source_root = Path(row["source_root"].strip())
        source_class = row["source_class"].strip()
        canonical_class = row["canonical_class"].strip()
        if not source_root.is_dir() or not source_class or not canonical_class:
            print(f"Skipping invalid mapping row: {row}")
            continue
        class_folder = source_root / source_class
        if not class_folder.is_dir():
            print(f"WARNING: source class folder does not exist: {class_folder}")
            continue
        for image_path in class_folder.rglob("*"):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest in seen:
                print(f"Skipping exact duplicate: {image_path} (already copied from {seen[digest]})")
                continue
            seen[digest] = str(image_path)
            destination_folder = output_root / canonical_class
            destination_folder.mkdir(parents=True, exist_ok=True)
            destination = destination_folder / f"{source_root.name}_{image_path.name}"
            if destination.exists():
                destination = destination_folder / f"{digest[:12]}_{image_path.name}"
            shutil.copy2(image_path, destination)
            copied += 1
    if copied == 0:
        raise SystemExit("No images were copied. Check the mapping CSV and downloaded folder paths.")
    print(f"Copied {copied} unique images into {output_root.resolve()}")
    print("Before training, inspect every canonical class and verify that mapped labels are scientifically compatible.")


if __name__ == "__main__":
    main()
