"""Markdown builder module for creating and saving Markdown documents."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownBuilder:
    """Builds and saves Markdown documents."""

    def __init__(self, backup_dir: Optional[str] = None, retention_days: int = 30):
        """
        Initialize MarkdownBuilder.

        Args:
            backup_dir: Directory for markdown backups (default: project_root/data/markdown_backup)
            retention_days: Number of days to retain backup files (default: 30)
        """
        if backup_dir is None:
            project_root = Path(__file__).parent.parent.parent.resolve()
            backup_dir = project_root / "data" / "markdown_backup"
        else:
            backup_dir = Path(backup_dir)

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        logger.info(f"MarkdownBuilder initialized with backup dir: {backup_dir}, retention: {retention_days} days")

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

            # Clean up old backup files
            self._cleanup_old_backups()

            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save Markdown: {e}")
            raise

    def _cleanup_old_backups(self) -> None:
        """
        Delete backup files older than retention_days.
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0

            for file_path in self.backup_dir.glob("*.md"):
                # Get file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {file_path.name}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup file(s) (older than {self.retention_days} days)")

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

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
