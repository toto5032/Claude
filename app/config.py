from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://app:app-secret@localhost:5432/app"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30

    model_config = {"env_prefix": "APP_"}


settings = Settings()
