"""Error handling utilities with custom exceptions and retry logic."""

import time
from functools import wraps
from typing import Callable, Type, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)


# Custom exceptions

class TelegramError(Exception):
    """Base exception for Telegram-related errors."""
    pass


class TelegramConnectionError(TelegramError):
    """Telegram connection failed."""
    pass


class TelegramAuthError(TelegramError):
    """Telegram authentication failed."""
    pass


class GeminiAPIError(Exception):
    """Base exception for Gemini API errors."""
    pass


class GeminiRateLimitError(GeminiAPIError):
    """Gemini API rate limit exceeded."""
    pass


class GoogleDocsError(Exception):
    """Base exception for Google Docs errors."""
    pass


class GoogleDocsAuthError(GoogleDocsError):
    """Google Docs authentication failed."""
    pass


class ProcessingError(Exception):
    """Base exception for processing errors."""
    pass


# Retry decorator

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function on error with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry

    Example:
        @retry_on_error(max_retries=3, delay=1.0, exceptions=(ConnectionError,))
        def my_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed, re-raise
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise

                    # Log and retry
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")

                    time.sleep(current_delay)
                    current_delay *= backoff

            return None

        return wrapper
    return decorator


# Async retry decorator

def async_retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry an async function on error with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio

            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed, re-raise
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise

                    # Log and retry
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            return None

        return wrapper
    return decorator


# Error context manager

class ErrorContext:
    """
    Context manager for handling errors in a specific context.

    Example:
        with ErrorContext("Processing chat"):
            # Code that might fail
            process_chat()
    """

    def __init__(self, context_name: str, raise_on_error: bool = True):
        """
        Initialize error context.

        Args:
            context_name: Name of the context for logging
            raise_on_error: Whether to re-raise exceptions (default: True)
        """
        self.context_name = context_name
        self.raise_on_error = raise_on_error

    def __enter__(self):
        logger.debug(f"Entering context: {self.context_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Error in {self.context_name}: {exc_type.__name__}: {exc_val}"
            )

            if not self.raise_on_error:
                # Suppress exception
                logger.info(f"Suppressing exception in {self.context_name}")
                return True

        return False
