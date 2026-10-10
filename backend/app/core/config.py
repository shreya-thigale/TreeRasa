"""Central configuration, loaded from backend/.env or environment variables."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    database_url: str = "sqlite:///./treerasa_dev.db"
    jwt_secret_key: str = "development-only-secret-change-this-before-use-32chars"
    jwt_expire_minutes: int = 1440
    upload_dir: str = "uploads"
    model_path: str = "model_artifacts/plant_disease_model.keras"
    labels_path: str = "model_artifacts/class_names.json"
    pest_model_path: str = "model_artifacts/pest/plant_pest_model.keras"
    pest_labels_path: str = "model_artifacts/pest/plant_pest_model_class_names.json"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 12
    prediction_min_confidence: float = 0.65
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    def backend_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

settings = Settings()
