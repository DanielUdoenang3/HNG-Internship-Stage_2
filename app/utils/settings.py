from pydantic_settings import BaseSettings
from decouple import config
from pathlib import Path

# Use this to build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    """Class to hold application's config values."""

    DB_URL: str = config("DB_URL")

settings = Settings()