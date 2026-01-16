"""Gemini API client module for AI-powered content processing."""

from typing import Optional

import google.generativeai as genai

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        """
        Initialize Gemini API client.

        Args:
            api_key: Gemini API key
            model_name: Model to use (default: gemini-flash-latest)
        """
        self.api_key = api_key
        self.model_name = model_name

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(model_name)

        logger.info(f"GeminiClient initialized with model: {model_name}")

    def generate_content(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate content using Gemini API.

        Args:
            prompt: Text prompt for generation
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Generated text or None if failed

        Raises:
            Exception: If API call fails after all retries
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")

                response = self.model.generate_content(prompt)

                if not response or not response.text:
                    logger.warning("Gemini API returned empty response")
                    continue

                logger.info(f"Gemini API call successful (response length: {len(response.text)} chars)")
                return response.text

            except Exception as e:
                error_msg = str(e).lower()

                # Check for rate limit errors
                if "quota" in error_msg or "rate limit" in error_msg:
                    logger.error(f"Gemini API rate limit exceeded: {e}")
                    raise Exception(
                        "Gemini API rate limit exceeded. "
                        "Free tier allows 20 requests per day. "
                        "Please try again tomorrow."
                    )

                # Check for authentication errors
                if "api key" in error_msg or "authentication" in error_msg:
                    logger.error(f"Gemini API authentication failed: {e}")
                    raise Exception(
                        "Gemini API authentication failed. "
                        "Please check your GEMINI_API_KEY in .env file."
                    )

                # Log other errors
                logger.warning(f"Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")

                # Retry on transient errors
                if attempt < max_retries - 1:
                    logger.info("Retrying...")
                    continue
                else:
                    logger.error(f"Gemini API call failed after {max_retries} attempts")
                    raise

        return None

    def check_api_key(self) -> bool:
        """
        Verify that the API key is valid.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try a minimal API call to verify the key
            response = self.model.generate_content("test", request_options={"timeout": 10})
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
