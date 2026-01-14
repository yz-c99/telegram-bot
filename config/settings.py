"""Settings management module for loading environment variables and YAML configuration."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv


class Settings:
    """Settings class for managing environment variables and YAML configuration."""

    def __init__(self, env_path: Optional[str] = None, yaml_path: Optional[str] = None):
        """
        Initialize settings by loading .env and YAML configuration.

        Args:
            env_path: Path to .env file (default: project_root/.env)
            yaml_path: Path to YAML config (default: project_root/config/target_chats.yaml)
        """
        # Determine project root (parent of config directory)
        self.project_root = Path(__file__).parent.parent.resolve()

        # Load environment variables
        if env_path is None:
            env_path = self.project_root / ".env"
        load_dotenv(env_path)

        # Load YAML configuration
        if yaml_path is None:
            yaml_path = self.project_root / "config" / "target_chats.yaml"

        with open(yaml_path, "r", encoding="utf-8") as f:
            self.yaml_config = yaml.safe_load(f)

        # Load environment variables
        self._load_env_vars()

    def _load_env_vars(self) -> None:
        """Load and validate environment variables."""
        # Telegram settings
        self.telegram_api_id = os.getenv("TELEGRAM_API_ID")
        self.telegram_api_hash = os.getenv("TELEGRAM_API_HASH")
        self.telegram_phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")

        # Gemini API settings
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Google Docs settings
        self.google_credentials_path = os.getenv(
            "GOOGLE_CREDENTIALS_PATH",
            "./credentials/google_credentials.json"
        )

        # Execution settings
        self.timezone = os.getenv("TIMEZONE", "Asia/Tokyo")
        self.execution_time = os.getenv("EXECUTION_TIME", "09:00")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    @property
    def target_chats(self) -> List[Dict]:
        """Get list of target chats from YAML configuration."""
        return self.yaml_config.get("target_chats", [])

    @property
    def enabled_chats(self) -> List[Dict]:
        """Get list of enabled chats only."""
        return [chat for chat in self.target_chats if chat.get("enabled", False)]

    @property
    def filters(self) -> Dict:
        """Get filter settings from YAML configuration."""
        return self.yaml_config.get("filters", {})

    @property
    def min_message_length(self) -> int:
        """Get minimum message length filter."""
        return self.filters.get("min_message_length", 10)

    @property
    def exclude_patterns(self) -> List[str]:
        """Get exclude patterns for filtering."""
        return self.filters.get("exclude_patterns", [])

    def validate(self) -> None:
        """
        Validate that required settings are present.

        Raises:
            ValueError: If required settings are missing
        """
        required_env_vars = [
            ("TELEGRAM_API_ID", self.telegram_api_id),
            ("TELEGRAM_API_HASH", self.telegram_api_hash),
            ("TELEGRAM_PHONE_NUMBER", self.telegram_phone_number),
            ("GEMINI_API_KEY", self.gemini_api_key),
        ]

        missing_vars = [name for name, value in required_env_vars if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please set them in your .env file"
            )

        # Validate at least one enabled chat exists
        if not self.enabled_chats:
            raise ValueError(
                "No enabled chats found in config/target_chats.yaml\n"
                "Please add at least one chat with 'enabled: true'"
            )
