# TreeRasa backend

FastAPI + SQLAlchemy backend. The API is split by feature so students can follow a request from route to model/service and database.

## Run

1. Start PostgreSQL from the repository root: `docker compose up -d postgres`.
2. In this folder, create `.env` from `.env.example` and set the password in `DATABASE_URL` to match the root `.env` file.
3. Create/activate a virtual environment and install `pip install -r requirements.txt`.
4. Start the API from this folder: `uvicorn app.main:app --reload --port 8000`.
5. Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

Tables are created automatically for this student MVP. Use Alembic migrations before production.

## Main folders

- `app/api/routes/`: endpoint logic grouped by feature.
- `app/models/`: PostgreSQL table definitions.
- `app/core/`: settings and password/token helpers.
- `app/db/`: engine and request-scoped database sessions.
- `app/services/`: trained-model inference and conservative guidance.
- `uploads/`: user files, excluded from version control.
- `model_artifacts/`: trained model files, excluded from version control.

When model artifacts are missing, scans are saved with `model_not_trained`. The API does not invent a disease prediction.
