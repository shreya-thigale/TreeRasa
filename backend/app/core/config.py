from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://treerasa:change_me@localhost:5432/treerasa"
    jwt_secret_key: str = "CHANGE_ME_BEFORE_DEPLOYMENT"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
