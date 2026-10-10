# TreeRasa image-model training

This guide describes the one supported training workflow in the `ml/` folder. It is written for a beginner team, and it intentionally does not download datasets or invent labels for you.

## 1. Dataset sources to review

Do not combine every dataset blindly. Disease classification, insect-pest recognition, nutrient deficiency detection and image-region segmentation are different tasks. Check each source's licence, crop coverage, labels, capture conditions and permitted academic/commercial use before downloading.

| Dataset / source | Best initial use | Important checks |
|---|---|---|
| [PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset) | Baseline leaf-disease classifier | Controlled images are useful for a baseline but don't represent every field condition. Review licence and attribution. |
| [PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset) | More varied, real-world disease photos | Label meanings may not map exactly to PlantVillage. Review permissions and labels. |
| [Plant Pathology 2020 / FGVC7](https://www.kaggle.com/c/plant-pathology-2020-fgvc7/data) | Apple-leaf disease benchmark | Kaggle access and competition terms apply. |
| [Plant Pathology 2021 / FGVC8](https://www.kaggle.com/c/plant-pathology-2021-fgvc8/data) | Additional apple-leaf benchmark | Some labels are multi-label; do not force them into single-label folders without a reviewed conversion plan. |
| [Cassava Leaf Disease](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/data) | Cassava-specific disease categories | Crop-specific task; inspect the class definitions. |
| [Paddy Disease Classification](https://www.kaggle.com/competitions/paddy-disease-classification/data) | Rice/paddy leaf disease | Review labels and competition rules. |
| [Rice leaf diseases](https://www.kaggle.com/datasets/vbookshelf/rice-leaf-diseases) | Rice disease experiments | Confirm the uploader's licence, label quality and duplicates. |
| [New Plant Diseases Dataset](https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset) | Additional class-folder images | May overlap with PlantVillage-derived material; deduplicate and document provenance. |
| [AI Challenger 2018](https://github.com/AIChallenger/AI_Challenger_2018) | Candidate crop-disease dataset | Inspect download instructions, label ontology and current terms. |
| [IP102](https://github.com/xpwu95/IP102) | Separate insect-pest classifier | Pest recognition is a separate task. Keep its classes and model separate from disease classes. |
| [Kaggle plant-disease discovery](https://www.kaggle.com/datasets?search=plant+disease) | Find more crop-specific datasets | Quality and licensing vary by uploader; prefer original author sources. |
| [Hugging Face plant-disease discovery](https://huggingface.co/datasets?search=plant%20disease) | Research dataset discovery | Read each dataset card, licence, split and label definitions. |

This list is a starting shortlist, not a claim that every source is currently downloadable or suitable for every use. No dataset is bundled in this ZIP. Never redistribute a downloaded dataset unless its terms permit it.

For leaf-region highlighting, investigate [plant disease segmentation datasets](https://www.kaggle.com/datasets?search=plant+disease+segmentation) and relevant research repositories separately. A classifier returns a class for the whole image; it does not locate diseased pixels. Segmentation needs a separate dataset, model and evaluation plan.

## 2. Use the correct Python environment

For the TensorFlow dependency range in this project, Python 3.11 is a safe default. From the repository root:

```bash
cd backend
python3.11 -m venv .venv-ml
source .venv-ml/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-ml.txt
cd ..
```

If your Mac does not have `python3.11`, install it using the official Python installer or an environment manager your team already knows. Use the same active environment when running the training command.

## 3. Prepare a labelled baseline

Download and review PlantVillage first. Keep the original download separate. The input structure should contain one subfolder per reviewed class label:

```text
raw_dataset/
├── Tomato___healthy/
│   ├── image_001.jpg
│   └── image_002.jpg
└── Tomato___Early_blight/
    ├── image_003.jpg
    └── image_004.jpg
```

If the archive has an extra parent directory, pass the actual folder path to the script. If labels are supplied in a CSV or multi-label format, review the mapping and convert them intentionally rather than guessing.

Run from the repository root:

```bash
python ml/prepare_dataset.py --source raw_dataset --output dataset --seed 42
```

The default split is approximately 70% train, 15% validation and 15% test. Exact duplicate files are skipped. The script warns about small classes and stops if a class has fewer than three unique images. It cannot detect near-duplicates or different photos of the same plant. For a stronger evaluation, keep entire farms, capture sessions or source datasets out of the test split when possible.

## 4. Combining multiple datasets safely

Use `ml/combine_datasets.py` only after reviewing which labels truly mean the same thing. Copy `ml/label_map.example.csv` to `label_map.csv`, then add real paths and explicit class mappings. The mapping columns are `source_root,source_class,canonical_class`.

Example format only (replace the paths and labels with folders you have verified):

```csv
source_root,source_class,canonical_class
downloads/PlantVillage/PlantVillage,Tomato___healthy,tomato_healthy
downloads/PlantVillage/PlantVillage,Tomato___Early_blight,tomato_early_blight
```

Run:

```bash
python ml/combine_datasets.py --mapping label_map.csv --output raw_dataset
python ml/prepare_dataset.py --source raw_dataset --output dataset --seed 42
```

Do not merge pest classes with disease classes. Do not map generic labels such as `unhealthy` to a specific disease without scientific support. The combined output must be reviewed before training.

## 5. Train the model

The classifier uses MobileNetV2 transfer learning. Training augmentation, class weighting, validation-based checkpointing, early stopping and learning-rate reduction are included.

```bash
python ml/train_model.py --data-root dataset --epochs 12
```

After checking the first run, you can optionally fine-tune the final backbone layers:

```bash
python ml/train_model.py --data-root dataset --epochs 12 --fine-tune-epochs 3
```

The first run may need internet access to download MobileNetV2's ImageNet weights. On a laptop, use a smaller reviewed subset or reduce `--batch-size` if memory is limited. Do not tune repeatedly against the test set.

## 6. Output artifacts

Artifacts are written to `backend/model_artifacts/`, which matches the API configuration:

- `plant_disease_model.keras` — trained Keras model.
- `class_names.json` — exact model output index-to-class mapping.
- `plant_disease_model_training_history.csv` — training and validation metrics by epoch.
- `plant_disease_model_evaluation_summary.json` — held-out test loss, accuracy, seed and evaluation note.
- `plant_disease_model_test_report.txt` and `.json` — per-class precision, recall and F1.
- `plant_disease_model_confusion_matrix.csv` and `.png` — class errors.
- `dataset_counts.json` — per-class training counts.

Review per-class recall and macro-F1, not accuracy alone. Inspect false positives and false negatives. The API only classifies leaf images, and low-confidence results are marked uncertain using `PREDICTION_MIN_CONFIDENCE` in `backend/.env`.

## 7. Important degree-project limitations

- A leaf classifier should not claim to diagnose stems, roots, flowers or fruits. Those parts need suitable labelled images and independent validation.
- A confidence value is not calibrated diagnostic certainty.
- A disease label must not automatically become a fertilizer prescription. Nutrient recommendations require crop, growth stage, region, soil/tissue results, units and agronomic rules.
- Build a separate pest-recognition model unless a validated dataset supports a deliberately designed multi-task model.
- The current model classifies the whole image. It does not outline diseased regions; that requires a segmentation/detection dataset and model.
- Do not report an accuracy score until training and final evaluation actually finish. Then evaluate on independent field photos from different farms, phones, seasons and lighting.
