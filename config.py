from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "gemini"  # claude | openai | gemini
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_gemini_api_key: str = ""

    home_location: str = ""  # fallback if not provided in request


settings = Settings()
