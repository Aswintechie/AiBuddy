"""
config.py - Configuration management for AiBuddy bot.

Loads and validates all required environment variables, providing
a single Config class used throughout the application.
"""

import os
import logging
from dotenv import load_dotenv

# Load .env file if present (useful for local development)
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration loaded from environment variables.

    Raises:
        ValueError: If any required environment variable is missing.
    """

    def __init__(self) -> None:
        """Load and validate all configuration values."""
        # Required secrets – raise clearly if missing
        self._app_id: str = self._require("MICROSOFT_APP_ID")
        self._app_password: str = self._require("MICROSOFT_APP_PASSWORD")
        self._groq_api_key: str = self._require("GROQ_API_KEY")

        # Optional / defaulted values
        self._groq_model: str = os.environ.get(
            "GROQ_MODEL", "llama-3.3-70b-versatile"
        )
        self._port: int = int(os.environ.get("PORT", "8080"))
        self._log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require(name: str) -> str:
        """Return the value of *name* or raise :class:`ValueError`."""
        value = os.environ.get(name)
        if not value:
            raise ValueError(
                f"Required environment variable '{name}' is not set. "
                "Copy .env.example to .env and fill in your credentials."
            )
        return value

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def APP_ID(self) -> str:
        """Microsoft Bot App ID (Azure registration)."""
        return self._app_id

    @property
    def APP_PASSWORD(self) -> str:
        """Microsoft Bot App Password (Azure registration)."""
        return self._app_password

    @property
    def GROQ_API_KEY(self) -> str:
        """Groq API key for Llama 3 inference."""
        return self._groq_api_key

    @property
    def GROQ_MODEL(self) -> str:
        """Groq model identifier (default: llama-3.3-70b-versatile)."""
        return self._groq_model

    @property
    def PORT(self) -> int:
        """TCP port the aiohttp server will bind to (default: 8080)."""
        return self._port

    @property
    def LOG_LEVEL(self) -> str:
        """Python logging level string (default: INFO)."""
        return self._log_level
