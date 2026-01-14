#!/usr/bin/env python3
"""Main entry point for Telegram to Google Docs Auto-Collector."""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.ai_processor.content_organizer import ContentOrganizer
from src.ai_processor.gemini_client import GeminiClient
from src.document.google_docs_client import GoogleDocsClient
from src.document.markdown_builder import MarkdownBuilder
from src.filters.content_filter import filter_messages
from src.storage.state_manager import StateManager
from src.telegram_client.client import TelegramClient
from src.telegram_client.message_fetcher import MessageFetcher
from src.telegram_client.message_reader import MessageReader
from src.utils.error_handler import (
    ErrorContext,
    GeminiRateLimitError,
    ProcessingError,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def process_chat(
    chat_config: Dict,
    telegram_client: TelegramClient,
    state_manager: StateManager,
    dry_run: bool = False
) -> List[Dict]:
    """
    Process a single chat: fetch new messages and mark as read.

    Args:
        chat_config: Chat configuration dictionary
        telegram_client: Connected Telegram client
        state_manager: State manager instance
        dry_run: If True, don't mark messages as read or update state

    Returns:
        List of new messages
    """
    chat_id = chat_config.get("chat_id")
    chat_name = chat_config.get("name", chat_id)

    logger.info(f"Processing chat: {chat_name} ({chat_id})")

    # Initialize fetcher and reader
    fetcher = MessageFetcher(telegram_client.client)
    reader = MessageReader(telegram_client.client)

    # Get last processed message ID
    last_message_id = state_manager.get_last_message_id(chat_id)

    if last_message_id:
        logger.info(f"Last processed message ID: {last_message_id}")
    else:
        logger.info("First run for this chat - will fetch last 24 hours")

    # Fetch new messages
    messages = await fetcher.fetch_new_messages(chat_id, last_message_id)

    if not messages:
        logger.info(f"No new messages in {chat_name}")
        return []

    logger.info(f"Fetched {len(messages)} new messages from {chat_name}")

    # Get latest message ID for state update
    latest_message_id = max(msg["message_id"] for msg in messages)

    if not dry_run:
        # Mark messages as read
        try:
            await reader.mark_as_read(chat_id, latest_message_id)
            logger.info(f"Marked messages as read up to ID {latest_message_id}")
        except Exception as e:
            logger.warning(f"Failed to mark messages as read: {e}")

        # Update state
        state_manager.update_message_id(chat_id, latest_message_id, chat_name)
        logger.info(f"Updated state with latest message ID: {latest_message_id}")
    else:
        logger.info("[DRY RUN] Would mark messages as read and update state")

    return messages


async def main_async(args) -> int:
    """
    Main async function that orchestrates the entire workflow.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    start_time = time.time()

    try:
        # Load settings
        logger.info("Loading settings...")
        settings = Settings()

        # Validate settings (skip in dry-run mode)
        if not args.dry_run:
            settings.validate()

        logger.info(f"Loaded {len(settings.enabled_chats)} enabled chat(s)")

        # Initialize components
        logger.info("Initializing components...")
        state_manager = StateManager()

        # Check Gemini API rate limit
        if not args.dry_run:
            api_calls_today = state_manager.get_gemini_api_call_count_today()
            logger.info(f"Gemini API calls today: {api_calls_today}/20")

            if api_calls_today >= 20:
                logger.error("Gemini API rate limit reached (20 calls/day)")
                raise GeminiRateLimitError(
                    "Daily Gemini API limit reached. Please try again tomorrow."
                )

        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        telegram_client = TelegramClient(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            phone_number=settings.telegram_phone_number
        )

        async with telegram_client:
            logger.info("Connected to Telegram successfully")

            # Collect messages from all chats
            all_messages = []

            for chat_config in settings.enabled_chats:
                with ErrorContext(
                    f"Processing chat {chat_config.get('name')}",
                    raise_on_error=False  # Continue with other chats if one fails
                ):
                    messages = await process_chat(
                        chat_config,
                        telegram_client,
                        state_manager,
                        dry_run=args.dry_run
                    )
                    all_messages.extend(messages)

            logger.info(f"Total messages collected: {len(all_messages)}")

            if not all_messages:
                logger.info("No new messages to process")

                # Log this run
                if not args.dry_run and not args.test:
                    state_manager.add_processing_log(
                        execution_date=datetime.now().date().isoformat(),
                        total_messages=0,
                        filtered_messages=0,
                        status="SUCCESS",
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )

                return 0

        # Filter messages
        logger.info("Filtering messages...")
        filtered_messages = filter_messages(all_messages, settings.filters)
        logger.info(f"Messages after filtering: {len(filtered_messages)}")

        if not filtered_messages:
            logger.info("No messages remaining after filtering")

            # Log this run
            if not args.dry_run and not args.test:
                state_manager.add_processing_log(
                    execution_date=datetime.now().date().isoformat(),
                    total_messages=len(all_messages),
                    filtered_messages=0,
                    status="SUCCESS",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            return 0

        # Process with Gemini AI
        if args.dry_run:
            logger.info("[DRY RUN] Would organize messages with Gemini AI")
            organized_content = f"# Dry Run\n\n{len(filtered_messages)} messages would be processed"
        else:
            logger.info("Organizing messages with Gemini AI...")
            gemini_client = GeminiClient(api_key=settings.gemini_api_key)
            organizer = ContentOrganizer(gemini_client)
            organized_content = organizer.organize_messages(filtered_messages)
            logger.info("Messages organized successfully")

        # Save Markdown
        logger.info("Saving Markdown...")
        markdown_builder = MarkdownBuilder()
        markdown_path = markdown_builder.save_markdown(organized_content)
        logger.info(f"Markdown saved to: {markdown_path}")

        # Upload to Google Docs
        document_id = None
        document_url = None

        if args.dry_run:
            logger.info("[DRY RUN] Would upload to Google Docs")
        elif args.test:
            logger.info("[TEST MODE] Skipping Google Docs upload")
        else:
            logger.info("Uploading to Google Docs...")
            try:
                google_docs_client = GoogleDocsClient()
                doc_title = f"Telegram Messages - {datetime.now().strftime('%Y-%m-%d')}"
                doc_info = google_docs_client.create_document(doc_title, organized_content)

                document_id = doc_info["document_id"]
                document_url = doc_info["document_url"]

                logger.info(f"Document created: {document_url}")

            except Exception as e:
                logger.error(f"Failed to upload to Google Docs: {e}")
                # Continue anyway - we have the Markdown backup

        # Record processing log
        if not args.dry_run and not args.test:
            processing_time_ms = int((time.time() - start_time) * 1000)

            state_manager.add_processing_log(
                execution_date=datetime.now().date().isoformat(),
                total_messages=len(all_messages),
                filtered_messages=len(filtered_messages),
                status="SUCCESS",
                document_id=document_id,
                document_url=document_url,
                processing_time_ms=processing_time_ms
            )

            logger.info(f"Processing complete in {processing_time_ms}ms")

        # Final summary
        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("Processing Summary")
        logger.info("=" * 60)
        logger.info(f"Total messages collected: {len(all_messages)}")
        logger.info(f"Messages after filtering: {len(filtered_messages)}")
        logger.info(f"Markdown saved: {markdown_path}")
        if document_url:
            logger.info(f"Google Doc URL: {document_url}")
        logger.info(f"Processing time: {elapsed_time:.2f} seconds")
        logger.info("=" * 60)

        return 0

    except GeminiRateLimitError as e:
        logger.error(f"Rate limit error: {e}")
        return 1

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)

        # Try to log the error
        try:
            if not args.dry_run and not args.test:
                state_manager = StateManager()
                state_manager.add_processing_log(
                    execution_date=datetime.now().date().isoformat(),
                    total_messages=0,
                    filtered_messages=0,
                    status="FAILED",
                    error_message=str(e),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
        except:
            pass

        return 1


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Telegram to Google Docs Auto-Collector"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: skip Google Docs upload"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run: don't mark messages as read or update state"
    )

    args = parser.parse_args()

    # Log mode
    if args.dry_run:
        logger.info("Running in DRY RUN mode")
    elif args.test:
        logger.info("Running in TEST mode")
    else:
        logger.info("Running in PRODUCTION mode")

    # Run async main
    exit_code = asyncio.run(main_async(args))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
