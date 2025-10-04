"""
Configuration module for Cluedo Custom application.
Loads environment variables and provides application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Cluedo Custom")
    MAX_PLAYERS: int = int(os.getenv("MAX_PLAYERS", "8"))

    # AI settings
    USE_OPENAI: bool = os.getenv("USE_OPENAI", "false").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Game settings
    MIN_PLAYERS: int = 3
    MIN_ROOMS: int = 6
    MAX_ROOMS: int = 12

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 7860

    # Game data file
    GAMES_FILE: str = "games.json"


settings = Settings()
