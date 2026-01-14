"""Markdown builder module for creating and saving Markdown documents."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownBuilder:
    """Builds and saves Markdown documents."""

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize MarkdownBuilder.

        Args:
            backup_dir: Directory for markdown backups (default: project_root/data/markdown_backup)
        """
        if backup_dir is None:
            project_root = Path(__file__).parent.parent.parent.resolve()
            backup_dir = project_root / "data" / "markdown_backup"
        else:
            backup_dir = Path(backup_dir)

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"MarkdownBuilder initialized with backup dir: {backup_dir}")

    def build_markdown(self, organized_content: str) -> str:
        """
        Build final Markdown content (currently just returns the organized content).

        Args:
            organized_content: Organized content from Gemini AI

        Returns:
            Final Markdown string
        """
        # For now, just return the organized content as-is
        # Future enhancements could add additional formatting, headers, etc.
        return organized_content

    def save_markdown(self, content: str, filename: Optional[str] = None) -> str:
        """
        Save Markdown content to a file.

        Args:
            content: Markdown content to save
            filename: Custom filename (default: auto-generated with timestamp)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telegram_messages_{timestamp}.md"

        file_path = self.backup_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Markdown saved to: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save Markdown: {e}")
            raise

    def get_backup_files(self, limit: int = 10) -> list:
        """
        Get list of backup Markdown files.

        Args:
            limit: Maximum number of files to return (default: 10)

        Returns:
            List of file paths, sorted by modification time (newest first)
        """
        try:
            files = sorted(
                self.backup_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            return [str(f) for f in files[:limit]]

        except Exception as e:
            logger.error(f"Failed to list backup files: {e}")
            return []
