"""Google Docs client module for creating and uploading documents."""

import os
import pickle
from pathlib import Path
from typing import Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.utils.logger import get_logger

logger = get_logger(__name__)

# If modifying these scopes, delete token.pickle
SCOPES = ['https://www.googleapis.com/auth/documents']


class GoogleDocsClient:
    """Client for creating and managing Google Docs documents."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        """
        Initialize Google Docs client.

        Args:
            credentials_path: Path to credentials.json (default: from env or ./credentials/google_credentials.json)
            token_path: Path to token.pickle (default: ./credentials/token.pickle)
        """
        # Determine credentials path
        if credentials_path is None:
            credentials_path = os.getenv(
                "GOOGLE_CREDENTIALS_PATH",
                "./credentials/google_credentials.json"
            )

        # Determine token path
        if token_path is None:
            project_root = Path(__file__).parent.parent.parent.resolve()
            token_path = project_root / "credentials" / "token.pickle"
        else:
            token_path = Path(token_path)

        self.credentials_path = credentials_path
        self.token_path = str(token_path)

        # Authenticate and build service
        self.creds = self._authenticate()
        self.service = build('docs', 'v1', credentials=self.creds)

        logger.info("GoogleDocsClient initialized")

    def _authenticate(self) -> Credentials:
        """
        Authenticate with Google OAuth 2.0.

        Returns:
            Credentials object

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If authentication fails
        """
        creds = None

        # Load existing token if available
        token_path = Path(self.token_path)
        if token_path.exists():
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing OAuth token")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed OAuth token")
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                # Need new authentication
                logger.error(
                    "No valid credentials found. "
                    "Please run scripts/setup_google.py to authenticate."
                )
                raise Exception(
                    "Not authenticated with Google Docs. "
                    "Please run scripts/setup_google.py first."
                )

            # Save the credentials for the next run
            try:
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Saved OAuth token")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        return creds

    def create_document(self, title: str, content: str) -> Dict:
        """
        Create a new Google Docs document with Markdown content.

        Args:
            title: Document title
            content: Markdown content to insert

        Returns:
            Dictionary with document_id and document_url

        Raises:
            Exception: If document creation fails
        """
        try:
            # Create empty document
            logger.info(f"Creating Google Doc: {title}")
            doc = self.service.documents().create(body={'title': title}).execute()
            doc_id = doc.get('documentId')

            logger.info(f"Document created with ID: {doc_id}")

            # Insert content
            self._insert_content(doc_id, content)

            # Generate document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

            logger.info(f"Document URL: {doc_url}")

            return {
                'document_id': doc_id,
                'document_url': doc_url,
            }

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise

    def _insert_content(self, doc_id: str, content: str) -> None:
        """
        Insert Markdown content into a Google Doc.

        Args:
            doc_id: Document ID
            content: Markdown content

        Note: This is a basic implementation that inserts content as plain text.
              For full Markdown → Google Docs formatting, a more sophisticated
              parser would be needed (which could be added in future iterations).
        """
        try:
            # For now, insert as plain text
            # Future enhancement: parse Markdown and apply formatting
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1,
                        },
                        'text': content
                    }
                }
            ]

            self.service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Content inserted into document {doc_id}")

        except Exception as e:
            logger.error(f"Failed to insert content: {e}")
            raise

    def update_document(self, doc_id: str, title: str, content: str) -> Dict:
        """
        Update an existing Google Docs document by replacing all content.

        Args:
            doc_id: Document ID to update
            title: New document title
            content: New Markdown content to replace existing content

        Returns:
            Dictionary with document_id and document_url

        Raises:
            Exception: If document update fails
        """
        try:
            logger.info(f"Updating Google Doc (ID: {doc_id})")

            # Get current document to find content length
            doc = self.service.documents().get(documentId=doc_id).execute()

            # Get the end index (total length of document)
            content_end_index = doc.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)

            # Prepare batch update requests
            requests = []

            # 1. Delete all existing content (except the first character at index 1)
            if content_end_index > 1:
                requests.append({
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': content_end_index - 1,
                        }
                    }
                })

            # 2. Insert new content
            requests.append({
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': content
                }
            })

            # Execute batch update
            self.service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Content updated in document {doc_id}")

            # Note: Google Docs API doesn't support updating document title after creation
            # The title is set only when the document is first created

            # Generate document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

            logger.info(f"Document URL: {doc_url}")

            return {
                'document_id': doc_id,
                'document_url': doc_url,
            }

        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    def get_document(self, doc_id: str) -> Dict:
        """
        Get document metadata.

        Args:
            doc_id: Document ID

        Returns:
            Document metadata dictionary
        """
        try:
            doc = self.service.documents().get(documentId=doc_id).execute()
            return doc
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise
