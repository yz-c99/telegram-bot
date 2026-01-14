"""Content filtering module for removing noise from Telegram messages."""

import re
from typing import Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


def filter_messages(messages: List[Dict], config: Dict) -> List[Dict]:
    """
    Filter messages based on configuration rules.

    Filtering rules:
    1. Remove messages shorter than min_message_length
    2. Remove messages matching exclude_patterns (regex)
    3. Remove system messages (no text content)

    Args:
        messages: List of message dictionaries
        config: Configuration dictionary with filters settings
            - min_message_length: Minimum message length (default: 10)
            - exclude_patterns: List of regex patterns to exclude

    Returns:
        List of filtered message dictionaries
    """
    if not messages:
        logger.info("No messages to filter")
        return []

    min_length = config.get("min_message_length", 10)
    exclude_patterns = config.get("exclude_patterns", [])

    # Compile regex patterns
    compiled_patterns = []
    for pattern in exclude_patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")

    filtered_messages = []
    stats = {
        "total": len(messages),
        "too_short": 0,
        "pattern_match": 0,
        "no_text": 0,
    }

    for message in messages:
        text = message.get("text", "")

        # Filter 1: Remove messages with no text (system messages)
        if not text or not text.strip():
            stats["no_text"] += 1
            continue

        # Filter 2: Remove messages shorter than minimum length
        if len(text.strip()) < min_length:
            stats["too_short"] += 1
            logger.debug(f"Filtered (too short): '{text[:30]}...'")
            continue

        # Filter 3: Remove messages matching exclude patterns
        matched = False
        for pattern in compiled_patterns:
            if pattern.match(text.strip()):
                stats["pattern_match"] += 1
                logger.debug(f"Filtered (pattern match): '{text[:30]}...' matched '{pattern.pattern}'")
                matched = True
                break

        if matched:
            continue

        # Message passed all filters
        filtered_messages.append(message)

    # Log filtering statistics
    filtered_count = stats["total"] - len(filtered_messages)
    logger.info(
        f"Filtered {filtered_count}/{stats['total']} messages "
        f"(too short: {stats['too_short']}, "
        f"pattern match: {stats['pattern_match']}, "
        f"no text: {stats['no_text']})"
    )

    return filtered_messages
