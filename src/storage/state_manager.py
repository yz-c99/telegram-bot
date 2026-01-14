"""State management module using SQLite for message_id tracking and processing logs."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """Manages application state using SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize StateManager and create database tables.

        Args:
            db_path: Path to SQLite database file (default: project_root/data/state.db)
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent.resolve()
            db_path = project_root / "data" / "state.db"
        else:
            db_path = Path(db_path)

        # Create data directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self._create_tables()
        logger.info(f"StateManager initialized with database: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create chat_state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_state (
                    chat_id TEXT PRIMARY KEY,
                    chat_name TEXT NOT NULL,
                    last_message_id INTEGER NOT NULL,
                    last_processed_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create processing_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_date TEXT NOT NULL,
                    total_messages INTEGER NOT NULL,
                    filtered_messages INTEGER NOT NULL,
                    themes_extracted INTEGER,
                    document_id TEXT,
                    document_url TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    processing_time_ms INTEGER,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()
            logger.debug("Database tables created/verified")

    def get_last_message_id(self, chat_id: str) -> Optional[int]:
        """
        Get the last processed message_id for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Last message_id or None if chat not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_message_id FROM chat_state WHERE chat_id = ?",
                (chat_id,)
            )
            row = cursor.fetchone()

            if row:
                message_id = row["last_message_id"]
                logger.debug(f"Retrieved last_message_id for {chat_id}: {message_id}")
                return message_id

            logger.debug(f"No last_message_id found for {chat_id}")
            return None

    def update_message_id(
        self,
        chat_id: str,
        message_id: int,
        chat_name: Optional[str] = None
    ) -> None:
        """
        Update the last processed message_id for a chat.

        Args:
            chat_id: Telegram chat ID
            message_id: New message_id to store
            chat_name: Name of the chat (optional, for display purposes)
        """
        now = datetime.now().isoformat()
        today = datetime.now().date().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if chat already exists
            cursor.execute(
                "SELECT chat_id FROM chat_state WHERE chat_id = ?",
                (chat_id,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing record
                cursor.execute("""
                    UPDATE chat_state
                    SET last_message_id = ?,
                        last_processed_date = ?,
                        updated_at = ?
                    WHERE chat_id = ?
                """, (message_id, today, now, chat_id))
                logger.info(f"Updated message_id for {chat_id}: {message_id}")
            else:
                # Insert new record
                if chat_name is None:
                    chat_name = chat_id

                cursor.execute("""
                    INSERT INTO chat_state (
                        chat_id,
                        chat_name,
                        last_message_id,
                        last_processed_date,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (chat_id, chat_name, message_id, today, now, now))
                logger.info(f"Created new chat_state for {chat_id}: {message_id}")

            conn.commit()

    def add_processing_log(
        self,
        execution_date: str,
        total_messages: int,
        filtered_messages: int,
        status: str,
        themes_extracted: Optional[int] = None,
        document_id: Optional[str] = None,
        document_url: Optional[str] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> int:
        """
        Add a processing log entry.

        Args:
            execution_date: Date of execution (ISO format)
            total_messages: Total number of messages collected
            filtered_messages: Number of messages after filtering
            status: Status of execution (SUCCESS, FAILED, PARTIAL)
            themes_extracted: Number of themes extracted (optional)
            document_id: Google Docs document ID (optional)
            document_url: Google Docs document URL (optional)
            error_message: Error message if status is FAILED (optional)
            processing_time_ms: Total processing time in milliseconds (optional)

        Returns:
            ID of the inserted log entry
        """
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_log (
                    execution_date,
                    total_messages,
                    filtered_messages,
                    themes_extracted,
                    document_id,
                    document_url,
                    status,
                    error_message,
                    processing_time_ms,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_date,
                total_messages,
                filtered_messages,
                themes_extracted,
                document_id,
                document_url,
                status,
                error_message,
                processing_time_ms,
                now
            ))

            log_id = cursor.lastrowid
            conn.commit()

            logger.info(
                f"Added processing log: {status} - "
                f"{total_messages} messages ({filtered_messages} after filter)"
            )
            return log_id

    def get_processing_history(self, days: int = 7) -> List[Dict]:
        """
        Get processing history for the last N days.

        Args:
            days: Number of days to retrieve (default: 7)

        Returns:
            List of processing log dictionaries
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    execution_date,
                    total_messages,
                    filtered_messages,
                    themes_extracted,
                    document_id,
                    document_url,
                    status,
                    error_message,
                    processing_time_ms,
                    created_at
                FROM processing_log
                WHERE execution_date >= ?
                ORDER BY created_at DESC
            """, (cutoff_date,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_gemini_api_call_count_today(self) -> int:
        """
        Get the number of Gemini API calls made today.

        Returns:
            Number of successful processing runs today
        """
        today = datetime.now().date().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM processing_log
                WHERE execution_date = ?
                AND status = 'SUCCESS'
            """, (today,))

            row = cursor.fetchone()
            count = row["count"] if row else 0

            logger.debug(f"Gemini API calls today: {count}")
            return count

    def close(self) -> None:
        """Close database connection (currently no-op as we use context managers)."""
        logger.debug("StateManager closed")
