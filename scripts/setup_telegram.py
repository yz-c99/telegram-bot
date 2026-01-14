#!/usr/bin/env python3
"""Setup script for Telegram authentication.

This script performs initial authentication with Telegram API and creates a session file.
Run this only once during initial setup.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from telethon import TelegramClient


async def setup_telegram():
    """Perform initial Telegram authentication."""
    print("=" * 60)
    print("Telegram Authentication Setup")
    print("=" * 60)
    print()

    # Load environment variables
    env_path = project_root / ".env"
    if not env_path.exists():
        print("❌ Error: .env file not found!")
        print(f"   Please create {env_path} based on .env.example")
        print()
        print("   Required variables:")
        print("   - TELEGRAM_API_ID")
        print("   - TELEGRAM_API_HASH")
        print("   - TELEGRAM_PHONE_NUMBER")
        return False

    load_dotenv(env_path)

    # Get credentials from environment
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")

    # Validate credentials
    if not all([api_id, api_hash, phone_number]):
        print("❌ Error: Missing required environment variables!")
        print()
        print("   Please set the following in your .env file:")
        if not api_id:
            print("   - TELEGRAM_API_ID")
        if not api_hash:
            print("   - TELEGRAM_API_HASH")
        if not phone_number:
            print("   - TELEGRAM_PHONE_NUMBER")
        return False

    print(f"✓ API ID: {api_id}")
    print(f"✓ API Hash: {api_hash[:8]}...")
    print(f"✓ Phone Number: {phone_number}")
    print()

    # Set up session directory
    session_dir = project_root / "data" / "telegram_session"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_path = str(session_dir / "telegram_session")

    print(f"Session file will be saved to: {session_path}")
    print()

    # Create Telegram client
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        print("Connecting to Telegram...")
        await client.connect()

        # Check if already authorized
        if await client.is_user_authorized():
            print()
            print("✓ Already authenticated!")
            print("  Session file already exists and is valid.")
            await client.disconnect()
            return True

        # Start authentication
        print()
        print("Starting authentication process...")
        print(f"Sending code to: {phone_number}")
        print()

        await client.send_code_request(phone_number)

        # Get authentication code from user
        code = input("Enter the authentication code you received: ").strip()

        try:
            await client.sign_in(phone_number, code)

        except Exception as e:
            # Handle two-factor authentication
            if "password" in str(e).lower():
                password = input("Two-factor authentication enabled. Enter your password: ").strip()
                await client.sign_in(password=password)
            else:
                raise

        print()
        print("✓ Authentication successful!")
        print(f"✓ Session file saved to: {session_path}.session")
        print()
        print("You can now run the main application.")

        await client.disconnect()
        return True

    except Exception as e:
        print()
        print(f"❌ Authentication failed: {e}")
        print()
        print("Please check your credentials and try again.")
        await client.disconnect()
        return False


def main():
    """Main entry point."""
    success = asyncio.run(setup_telegram())

    print()
    print("=" * 60)

    if success:
        print("Setup completed successfully!")
        print()
        print("Next steps:")
        print("  1. Configure target chats in config/target_chats.yaml")
        print("  2. Run: python scripts/test_connection.py")
        print("  3. Run: python src/main.py --test")
    else:
        print("Setup failed. Please fix the errors and try again.")

    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
