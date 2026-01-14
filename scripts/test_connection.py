#!/usr/bin/env python3
"""Test script to verify all API connections."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.ai_processor.gemini_client import GeminiClient
from src.document.google_docs_client import GoogleDocsClient
from src.storage.state_manager import StateManager
from src.telegram_client.client import TelegramClient


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()


def print_test(text: str, success: bool):
    """Print test result."""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {text}")


async def test_telegram(settings: Settings) -> bool:
    """Test Telegram connection."""
    print("Testing Telegram connection...")
    try:
        client = TelegramClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone_number=settings.telegram_phone_number
        )

        async with client:
            print_test("Telegram connection successful", True)
            print(f"  Session: telegram_session")
            return True

    except Exception as e:
        print_test(f"Telegram connection failed: {e}", False)
        print("  Please run: python scripts/setup_telegram.py")
        return False


def test_gemini(settings: Settings) -> bool:
    """Test Gemini API connection."""
    print()
    print("Testing Gemini API connection...")
    try:
        client = GeminiClient(api_key=settings.gemini_api_key)

        # Try a minimal API call
        response = client.generate_content("test", max_retries=1)

        if response:
            print_test("Gemini API connection successful", True)
            print(f"  Model: gemini-pro")
            return True
        else:
            print_test("Gemini API returned no response", False)
            return False

    except Exception as e:
        print_test(f"Gemini API connection failed: {e}", False)
        print("  Please check your GEMINI_API_KEY in .env")
        return False


def test_google_docs(settings: Settings) -> bool:
    """Test Google Docs connection."""
    print()
    print("Testing Google Docs connection...")
    try:
        client = GoogleDocsClient(credentials_path=settings.google_credentials_path)

        print_test("Google Docs authentication successful", True)
        print(f"  Credentials: {settings.google_credentials_path}")
        return True

    except Exception as e:
        print_test(f"Google Docs connection failed: {e}", False)
        print("  Please run: python scripts/setup_google.py")
        return False


def test_database() -> bool:
    """Test database connection."""
    print()
    print("Testing database connection...")
    try:
        state_manager = StateManager()

        # Test basic operations
        state_manager.update_message_id("test_connection", 999, "Test")
        last_id = state_manager.get_last_message_id("test_connection")

        if last_id == 999:
            print_test("Database connection successful", True)
            print(f"  Database: data/state.db")
            return True
        else:
            print_test("Database operation failed", False)
            return False

    except Exception as e:
        print_test(f"Database connection failed: {e}", False)
        return False


async def main():
    """Main test function."""
    print_header("Connection Test Suite")
    print("This script tests all API connections:")
    print("  - Telegram API")
    print("  - Gemini API")
    print("  - Google Docs API")
    print("  - SQLite Database")

    # Load settings
    print()
    print("Loading settings...")
    try:
        settings = Settings()
        print_test("Settings loaded", True)
    except Exception as e:
        print_test(f"Failed to load settings: {e}", False)
        print()
        print("Please ensure:")
        print("  1. .env file exists (copy from .env.example)")
        print("  2. All required variables are set")
        print("  3. config/target_chats.yaml exists")
        return 1

    # Run tests
    results = []

    # Test database (no credentials needed)
    results.append(("Database", test_database()))

    # Test Telegram
    results.append(("Telegram", await test_telegram(settings)))

    # Test Gemini API
    results.append(("Gemini API", test_gemini(settings)))

    # Test Google Docs
    results.append(("Google Docs", test_google_docs(settings)))

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        print_test(name, result)

    print()
    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✓ All connections successful!")
        print()
        print("You can now run:")
        print("  python src/main.py --test")
        return 0
    else:
        print("✗ Some connections failed")
        print()
        print("Please fix the failed connections before running the main script.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
