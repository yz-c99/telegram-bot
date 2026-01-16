"""Message fetching module for retrieving new Telegram messages."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.tl.types import Message

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MessageFetcher:
    """Handles fetching messages from Telegram chats."""

    def __init__(self, telegram_client: TelegramClient):
        """
        Initialize MessageFetcher.

        Args:
            telegram_client: Connected Telethon TelegramClient instance
        """
        self.client = telegram_client

    async def fetch_new_messages(
        self,
        chat_id: str,
        last_message_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch new messages from a chat since last_message_id.

        Args:
            chat_id: Chat identifier (username, phone number, or ID)
            last_message_id: Last processed message ID (None for initial run)

        Returns:
            List of message dictionaries with metadata

        Initial execution behavior:
            If last_message_id is None, fetches messages from the last 24 hours
        """
        try:
            # Get chat entity
            # Convert numeric chat_id to integer for group chats
            entity_id = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
            chat = await self.client.get_entity(entity_id)
            chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or str(chat_id)

            messages = []

            if last_message_id is None:
                # Initial execution: fetch last 24 hours
                logger.info(f"Initial fetch for {chat_name} - retrieving last 24 hours")
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

                async for message in self.client.iter_messages(chat, reverse=False):
                    if message.date < cutoff_time:
                        break

                    if message.message:  # Only text messages
                        msg_data = self._extract_message_data(message, chat_name)
                        messages.append(msg_data)

                logger.info(f"Initial fetch complete: {len(messages)} messages from {chat_name}")

            else:
                # Subsequent execution: fetch messages after last_message_id
                logger.info(f"Fetching messages after ID {last_message_id} from {chat_name}")

                async for message in self.client.iter_messages(
                    chat,
                    min_id=last_message_id,
                    reverse=False
                ):
                    # Skip the message with exactly last_message_id (already processed)
                    if message.id == last_message_id:
                        continue

                    if message.message:  # Only text messages
                        msg_data = self._extract_message_data(message, chat_name)
                        messages.append(msg_data)

                logger.info(f"Fetched {len(messages)} new messages from {chat_name}")

            return messages

        except Exception as e:
            logger.error(f"Failed to fetch messages from {chat_id}: {e}")
            raise

    def _extract_message_data(self, message: Message, chat_name: str) -> Dict:
        """
        Extract relevant data from a Telegram message.

        Args:
            message: Telethon Message object
            chat_name: Name of the chat

        Returns:
            Dictionary with message data
        """
        # Get sender information
        sender_name = "Unknown"
        if message.sender:
            first_name = getattr(message.sender, "first_name", None) or ""
            last_name = getattr(message.sender, "last_name", None) or ""
            sender_name = (first_name + " " + last_name).strip()
            if not sender_name:
                sender_name = getattr(message.sender, "username", None) or "Unknown"

        return {
            "message_id": message.id,
            "chat_id": message.chat_id,
            "chat_name": chat_name,
            "sender": sender_name,
            "text": message.message,
            "date": message.date.isoformat(),
            "timestamp": int(message.date.timestamp()),
        }

    async def get_latest_message_id(self, chat_id: str) -> Optional[int]:
        """
        Get the ID of the most recent message in a chat.

        Args:
            chat_id: Chat identifier

        Returns:
            Latest message ID or None if chat is empty
        """
        try:
            # Convert numeric chat_id to integer for group chats
            entity_id = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
            chat = await self.client.get_entity(entity_id)

            async for message in self.client.iter_messages(chat, limit=1):
                logger.debug(f"Latest message ID in {chat_id}: {message.id}")
                return message.id

            logger.warning(f"No messages found in {chat_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get latest message ID from {chat_id}: {e}")
            raise
