
### Optional pest model (separate labels)

After downloading and reviewing a permitted pest dataset, place its class folders under `raw_pest_dataset/`. Do not mix pest labels with disease labels. From the ML virtual environment in `backend/`:

```bash
python prepare_dataset.py --source raw_pest_dataset --output pest_dataset --seed 42
python train_model.py --data-root pest_dataset --output-dir model_artifacts/pest --model-name plant_pest_model --epochs 12
```

The pest model has a separate label file and API configuration. It remains an image classifier, not a bounding-box detector. If the task requires identifying exact insect locations, train and evaluate an object-detection model with box annotations separately.
