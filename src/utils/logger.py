"""Logging utility module for the application."""

import logging
import os
from pathlib import Path
from typing import Optional

import colorlog


# Global flag to ensure setup is done only once
_logging_configured = False


def setup_logging(log_level: str = "INFO", log_dir: Optional[str] = None) -> None:
    """
    Set up logging configuration with file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: project_root/logs)
    """
    global _logging_configured
    if _logging_configured:
        return

    # Determine log directory
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent.resolve()
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)

    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set log file path
    log_file = log_dir / "app.log"

    # Parse log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler (detailed format)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (colored format)
    console_formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    _logging_configured = True


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)
        log_level: Override log level from environment (optional)

    Returns:
        Logger instance
    """
    # Set up logging if not already configured
    if not _logging_configured:
        # Try to get log level from environment
        if log_level is None:
            log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level=log_level)

    return logging.getLogger(name)
