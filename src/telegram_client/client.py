"""Telegram client module for connecting to Telegram API."""

from pathlib import Path
from typing import Optional

from telethon import TelegramClient as TelethonClient
from telethon.sessions import StringSession

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """Wrapper for Telegram API client with session management."""

    def __init__(
        self,
        api_id: str,
        api_hash: str,
        phone_number: str,
        session_name: str = "telegram_session"
    ):
        """
        Initialize Telegram client.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: Phone number for authentication
            session_name: Name of session file (default: telegram_session)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number

        # Determine session file path
        project_root = Path(__file__).parent.parent.parent.resolve()
        session_dir = project_root / "data" / "telegram_session"
        session_dir.mkdir(parents=True, exist_ok=True)

        self.session_path = str(session_dir / session_name)

        # Initialize Telethon client
        self.client = TelethonClient(
            self.session_path,
            self.api_id,
            self.api_hash
        )

        self._connected = False
        logger.info(f"TelegramClient initialized with session: {session_name}")

    async def connect(self) -> None:
        """
        Connect to Telegram API.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            await self.client.connect()

            # Check if already authorized
            if not await self.client.is_user_authorized():
                logger.warning("User not authorized - please run setup_telegram.py first")
                raise ConnectionError(
                    "Not authorized. Please run scripts/setup_telegram.py to authenticate."
                )

            self._connected = True
            logger.info("Successfully connected to Telegram")

        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            raise ConnectionError(f"Telegram connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Telegram API."""
        if self._connected:
            await self.client.disconnect()
            self._connected = False
            logger.info("Disconnected from Telegram")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
