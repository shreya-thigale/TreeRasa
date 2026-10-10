# TreeRasa — Plant Health & Sustainable Care Platform

TreeRasa is a modular degree-project foundation built with **React + Vite**, **Python + FastAPI**, **PostgreSQL**, and **TensorFlow/Keras**. It supports plant records, leaf-image analysis, sustainable-care notes, lab reports, expert appointments, a community marketplace and database-backed workspace modules aligned with **SDG 15: Life on Land**.

The code is separated by responsibility: API routes handle HTTP requests, schemas validate inputs, models define database tables, services contain reusable logic, and React pages/components are split by feature.

## What works in this starter

- Registration/login with Argon2 password hashing and signed access tokens.
- PostgreSQL persistence for accounts, plants, scans, marketplace products/reviews, order requests, lab reports/measurements, doctor profiles, appointments, workspace records and audit events.
- Plant-library records, photo upload and live-camera capture, scan history, separate disease/pest model slots, confidence thresholding and explicit statuses when a model is missing or the plant part is unsupported.
- Farmer/gardener/vendor product listings, product ratings, stock-aware order requests, seller order updates, delivery-partner assignment and delivery-status steps. Payment gateways and external courier services are not connected.
- Lab-report uploads and manually entered measurements with limited, transparent rule-based educational notes. PDF/image reports are not automatically OCR-read.
- Plant doctor/agronomist/pathologist profiles and appointment requests.
- Database-backed CRUD workspaces for farms, nurseries, pest lifecycle notes, environmental readings, drone survey records, GIS observations, soil analyses, crop plans, explainability notes, biodiversity, recommendations, SDG 15 indicators, learning progress, reports, notifications and settings.
- Analytics derived from saved records, a records-backed GIS map, CSV/Excel/PDF exports, audit records and administrator-only user management.
- Responsive React UI, reusable components, dark/light theme and no fabricated farm records, scans, ratings or model-accuracy values.

## Model and feature limitations

No dataset or trained model is included. Your team must download permitted labelled datasets, review their labels/licences, run training and inspect the evaluation reports. The current classifier is whole-image classification and does not outline diseased regions. The disease model is for leaf images only; the pest classifier uses a separate model and label space. Non-leaf images are saved for review but not sent through the leaf classifier.

Treatment and lab notes are educational, not a confirmed diagnosis or crop-specific fertilizer/pesticide prescription. Botanical products can also harm plants, people and beneficial insects. Confirm important crop decisions with qualified local agricultural professionals.

## Beginner setup on macOS

### 1. Install prerequisites

Install Python 3.11, Node.js 20 LTS and Docker Desktop. Check the terminal commands:

```bash
python3 --version
node --version
npm --version
docker --version
```

### 2. Start PostgreSQL

From the extracted project root:

```bash
cd ~/Downloads/TreeRasa_Professional
cp .env.example .env
```

Set a local password in the root `.env`, then start the database:

```bash
docker compose up -d postgres
docker compose ps
```

### 3. Run the Python API

Open another Terminal tab/window:

```bash
cd backend
cp .env.example .env
```

If you changed `POSTGRES_PASSWORD` in the root `.env`, set the same password in `DATABASE_URL` inside `backend/.env`. Then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Tables are created automatically for this student MVP. Production needs database migrations, managed secrets, HTTPS, backups, monitoring and deployment hardening.

### 4. Run the React frontend

In a third Terminal tab/window:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. Camera capture generally requires localhost or HTTPS and browser permission.

### 5. Optional: create the first administrator

Public sign-up cannot create administrator accounts. From a backend terminal with the virtual environment active and database configured:

```bash
cd backend
source .venv/bin/activate
python create_admin.py
```

The script prompts for credentials interactively.

## Dataset sources and model training

Read [`ml/README.md`](ml/README.md) before downloading data. It covers PlantVillage, PlantDoc, Plant Pathology 2020/2021, Cassava Leaf Disease, Paddy Disease, AI Challenger, IP102 and discovery sources. These are sources to review, not files bundled with this project. Check each dataset's current licence, labels and permitted use; explicitly map labels before combining datasets.

Install the machine-learning dependencies in the backend virtual environment:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-ml.txt
cd ..
```

Place a reviewed dataset in one-subfolder-per-class format under `raw_dataset/`, then run from the repository root:

```bash
python ml/prepare_dataset.py --source raw_dataset --output dataset --seed 42
python ml/train_model.py --data-root dataset --epochs 12
```

For a separate pest classifier, prepare a pest-only dataset with the same split structure:

```bash
python ml/train_model.py --data-root pest_dataset --model-name plant_pest_model --output-dir backend/model_artifacts/pest --epochs 12
```

Training writes the model and evaluation artifacts under `backend/model_artifacts/`. Review held-out test accuracy, per-class precision/recall/F1 and the confusion matrix; then evaluate on independent real-world photos. Do not claim accuracy until training has completed. API predictions require both the model and matching class-label file.

## Folder guide

```text
TreeRasa_Professional/
├── docker-compose.yml             # Local PostgreSQL service
├── backend/app/api/routes/         # Feature endpoints
├── backend/app/core/               # Configuration and security
├── backend/app/db/                 # Database engine/session
├── backend/app/models/              # Database tables
├── backend/app/schemas/             # Input validation
├── backend/app/services/            # Inference, care guidance and audit helper
├── backend/model_artifacts/         # Trained models (not committed)
├── backend/uploads/                 # User uploads (not committed)
├── frontend/src/api/                # API client and authentication
├── frontend/src/components/         # Reusable UI components
├── frontend/src/pages/              # Feature-level React pages
├── frontend/src/styles/global.css   # Responsive design system
└── ml/                              # Dataset mapping, splitting and training
```

## Team conventions

- Keep `.env`, uploads, downloaded datasets, database dumps and trained model binaries out of Git.
- Make one branch per feature and test a user journey before merging.
- Add comments for non-obvious decisions, not every obvious line.
- Document dataset licences, class mappings, model metrics, limitations and member contributions for the degree-project report and viva.
