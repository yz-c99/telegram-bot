#!/usr/bin/env python3
"""Script to list all available Telegram chats with their IDs.

This script helps you find chat IDs to add to config/target_chats.yaml
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.telegram_client.client import TelegramClient


async def main():
    """Main function to list all chats."""
    print("=" * 60)
    print("Telegram Chat ID Finder")
    print("=" * 60)
    print()

    # Load settings
    try:
        settings = Settings()
    except Exception as e:
        print(f"✗ Failed to load settings: {e}")
        print()
        print("Please ensure:")
        print("  1. .env file exists with Telegram credentials")
        print("  2. You have run: python scripts/setup_telegram.py")
        return 1

    # Connect to Telegram
    print("Connecting to Telegram...")
    try:
        telegram_client = TelegramClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone_number=settings.telegram_phone_number
        )

        async with telegram_client:
            print("✓ Connected to Telegram")
            print()

            # Get all dialogs (chats)
            print("Fetching your chats...")
            print()

            dialogs = await telegram_client.client.get_dialogs()

            # Categorize chats
            channels = []
            groups = []
            users = []

            for dialog in dialogs:
                entity = dialog.entity

                # Determine chat type and ID
                chat_id = None
                chat_name = None
                chat_type = None

                if hasattr(entity, 'username') and entity.username:
                    # Channel or public group with username
                    chat_id = entity.username
                    chat_name = getattr(entity, 'title', entity.username)
                    chat_type = 'channel' if hasattr(entity, 'broadcast') and entity.broadcast else 'group'
                elif hasattr(entity, 'title'):
                    # Private group or channel
                    chat_id = str(entity.id)
                    chat_name = entity.title
                    chat_type = 'channel' if hasattr(entity, 'broadcast') and entity.broadcast else 'group'
                elif hasattr(entity, 'first_name'):
                    # User
                    chat_id = str(entity.id)
                    chat_name = entity.first_name
                    if hasattr(entity, 'last_name') and entity.last_name:
                        chat_name += f" {entity.last_name}"
                    chat_type = 'user'
                else:
                    continue

                # Add to appropriate list
                if chat_type == 'channel':
                    channels.append((chat_id, chat_name))
                elif chat_type == 'group':
                    groups.append((chat_id, chat_name))
                elif chat_type == 'user':
                    users.append((chat_id, chat_name))

            # Display results
            print("=" * 60)
            print(f"Found {len(channels) + len(groups) + len(users)} chats")
            print("=" * 60)

            # Channels
            if channels:
                print()
                print("📢 CHANNELS:")
                print("-" * 60)
                for chat_id, chat_name in channels:
                    print(f"  Chat ID: {chat_id}")
                    print(f"  Name:    {chat_name}")
                    print()

            # Groups
            if groups:
                print()
                print("👥 GROUPS:")
                print("-" * 60)
                for chat_id, chat_name in groups:
                    print(f"  Chat ID: {chat_id}")
                    print(f"  Name:    {chat_name}")
                    print()

            # Users (only show first 10)
            if users:
                print()
                print(f"💬 USERS (showing first 10 of {len(users)}):")
                print("-" * 60)
                for chat_id, chat_name in users[:10]:
                    print(f"  Chat ID: {chat_id}")
                    print(f"  Name:    {chat_name}")
                    print()

            # Instructions
            print()
            print("=" * 60)
            print("How to use these Chat IDs")
            print("=" * 60)
            print()
            print("Add chats to config/target_chats.yaml like this:")
            print()
            print("target_chats:")
            print("  - chat_id: \"YOUR_CHAT_ID\"")
            print("    name: \"Chat Display Name\"")
            print("    enabled: true")
            print()
            print("Example:")
            print("  - chat_id: \"example_channel\"")
            print("    name: \"My Channel\"")
            print("    enabled: true")
            print()

            return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Please ensure you have authenticated with Telegram:")
        print("  python scripts/setup_telegram.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
