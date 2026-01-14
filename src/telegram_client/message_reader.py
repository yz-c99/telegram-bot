"""Message reader module for marking Telegram messages as read."""

from typing import Optional

from telethon import TelegramClient

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MessageReader:
    """Handles marking Telegram messages as read."""

    def __init__(self, telegram_client: TelegramClient):
        """
        Initialize MessageReader.

        Args:
            telegram_client: Connected Telethon TelegramClient instance
        """
        self.client = telegram_client

    async def mark_as_read(self, chat_id: str, max_message_id: Optional[int] = None) -> None:
        """
        Mark messages as read in a chat up to a specific message ID.

        Args:
            chat_id: Chat identifier (username, phone number, or ID)
            max_message_id: Maximum message ID to mark as read (None = all messages)

        This uses Telegram's send_read_acknowledge() method to mark messages as read.
        """
        try:
            # Get chat entity
            chat = await self.client.get_entity(chat_id)
            chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or str(chat_id)

            # Send read acknowledgment
            if max_message_id is not None:
                await self.client.send_read_acknowledge(
                    chat,
                    max_id=max_message_id
                )
                logger.info(f"Marked messages as read in {chat_name} (up to ID {max_message_id})")
            else:
                await self.client.send_read_acknowledge(chat)
                logger.info(f"Marked all messages as read in {chat_name}")

        except Exception as e:
            logger.error(f"Failed to mark messages as read in {chat_id}: {e}")
            raise

    async def mark_chat_as_read(self, chat_id: str) -> None:
        """
        Mark all messages in a chat as read.

        Args:
            chat_id: Chat identifier (username, phone number, or ID)
        """
        await self.mark_as_read(chat_id, max_message_id=None)
