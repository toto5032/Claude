from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    debug: bool = False

    model_config = {"env_prefix": "APP_"}


settings = Settings()
