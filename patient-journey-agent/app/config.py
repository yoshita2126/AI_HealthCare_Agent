"""
Application configuration settings.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Patient Journey Agent"
    environment: str = os.getenv("ENV", "development")
    fhir_server_url: str = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
