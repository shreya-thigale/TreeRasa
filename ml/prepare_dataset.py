"""Prepare a reproducible train/validation/test split from labelled image folders.

Input example:
    raw_dataset/Apple___healthy/*.jpg
    raw_dataset/Apple___scab/*.jpg

Output example:
    dataset/train/Apple___healthy/*.jpg
    dataset/val/Apple___healthy/*.jpg
    dataset/test/Apple___healthy/*.jpg

The script copies source files and skips exact byte-for-byte duplicates. It cannot detect
near-duplicates or decide whether labels from two different datasets mean the same thing.
"""
from __future__ import annotations

import argparse
import hashlib
import random
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="raw_dataset", help="Folder containing one subfolder per class")
    parser.add_argument("--output", default="dataset", help="Destination for train/, val/ and test/")
    parser.add_argument("--train", type=float, default=0.70, help="Training fraction (default: 0.70)")
    parser.add_argument("--val", type=float, default=0.15, help="Validation fraction (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable splits")
    parser.add_argument("--minimum-per-class", type=int, default=10,
                        help="Warn when a class has fewer unique images (default: 10)")
    args = parser.parse_args()

    if args.train <= 0 or args.val <= 0 or args.train + args.val >= 1:
        raise SystemExit("Train and validation fractions must be positive and add up to less than 1.")

    source = Path(args.source)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output folder is not empty: {output}. Choose a new folder or clear it intentionally.")
    if not source.is_dir():
        raise SystemExit(f"Source folder not found: {source}. Read DATASETS_AND_TRAINING.md first.")

    class_folders = sorted(path for path in source.iterdir() if path.is_dir())
    if len(class_folders) < 2:
        raise SystemExit("At least two class subfolders are required.")

    randomizer = random.Random(args.seed)
    seen_hashes: dict[str, str] = {}
    report: dict[str, dict[str, int]] = {}

    for class_folder in class_folders:
        images = sorted(path for path in class_folder.rglob("*")
                        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        unique_images: list[Path] = []
        for image_path in images:
            file_hash = sha256_file(image_path)
            if file_hash in seen_hashes:
                print(f"Skipping exact duplicate: {image_path} (same bytes as {seen_hashes[file_hash]})")
                continue
            seen_hashes[file_hash] = str(image_path)
            unique_images.append(image_path)

        if len(unique_images) < args.minimum_per_class:
            print(f"WARNING: {class_folder.name} has only {len(unique_images)} unique images. "
                  "The test score may be unstable for this class.")
        if len(unique_images) < 3:
            raise SystemExit(f"Class '{class_folder.name}' needs at least 3 unique images to create all three splits.")

        randomizer.shuffle(unique_images)
        total = len(unique_images)
        train_count = max(1, int(total * args.train))
        validation_count = max(1, int(total * args.val))
        if train_count + validation_count >= total:
            train_count = total - 2
            validation_count = 1

        split_files = {
            "train": unique_images[:train_count],
            "val": unique_images[train_count:train_count + validation_count],
            "test": unique_images[train_count + validation_count:],
        }
        report[class_folder.name] = {}
        for split_name, files in split_files.items():
            destination_folder = output / split_name / class_folder.name
            destination_folder.mkdir(parents=True, exist_ok=True)
            for image_path in files:
                destination = destination_folder / image_path.name
                if destination.exists():
                    destination = destination_folder / f"{sha256_file(image_path)[:10]}_{image_path.name}"
                shutil.copy2(image_path, destination)
            report[class_folder.name][split_name] = len(files)

    print("\nPrepared dataset counts:")
    for class_name, counts in report.items():
        print(f"{class_name}: train={counts['train']}, val={counts['val']}, test={counts['test']}")
    print(f"\nTotal unique image bytes processed: {len(seen_hashes)}")
    print("\nResearch note: this is a baseline random split. For a strong evaluation, remove near-duplicates and "
          "keep entire farms, collection sessions or dataset sources out of the test set where possible.")


if __name__ == "__main__":
    main()
