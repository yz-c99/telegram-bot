"""Content organization module using Gemini AI for structuring Telegram messages."""

from datetime import datetime
from typing import Dict, List

from src.ai_processor.gemini_client import GeminiClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContentOrganizer:
    """Organizes Telegram messages into structured, thematic Markdown using Gemini AI."""

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize ContentOrganizer.

        Args:
            gemini_client: Initialized GeminiClient instance
        """
        self.gemini_client = gemini_client
        logger.info("ContentOrganizer initialized")

    def organize_messages(self, messages: List[Dict]) -> str:
        """
        Organize messages into structured Markdown optimized for NotebookLM.

        Args:
            messages: List of message dictionaries with text, sender, date, etc.

        Returns:
            Structured Markdown string organized by themes

        Raises:
            Exception: If Gemini API call fails
        """
        if not messages:
            logger.warning("No messages to organize")
            return self._create_empty_document()

        logger.info(f"Organizing {len(messages)} messages with Gemini AI")

        # Build the prompt
        prompt = self._build_prompt(messages)

        # Call Gemini API (single call for all messages)
        try:
            organized_content = self.gemini_client.generate_content(prompt)

            if not organized_content:
                logger.error("Gemini API returned empty content")
                return self._create_fallback_document(messages)

            logger.info("Successfully organized messages")
            return organized_content

        except Exception as e:
            logger.error(f"Failed to organize messages: {e}")
            raise

    def _build_prompt(self, messages: List[Dict]) -> str:
        """
        Build the prompt for Gemini API.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted prompt string
        """
        # Prepare messages text
        messages_text = []
        for i, msg in enumerate(messages, 1):
            chat_name = msg.get("chat_name", "Unknown")
            sender = msg.get("sender", "Unknown")
            date = msg.get("date", "")
            text = msg.get("text", "")

            # Format date for readability
            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = date

            messages_text.append(
                f"[{i}] {formatted_date} | {chat_name} | {sender}:\n{text}\n"
            )

        all_messages = "\n".join(messages_text)

        # Build prompt following PLANS.md specification
        prompt = f"""以下のTelegramメッセージをNotebookLMポッドキャスト用に整理してください。

要件:
1. 全メッセージをテーマごとに自動グループ化（テーマ数の制限なし）
2. 各テーマ内で時系列または論理的に整理
3. メタデータ付き構造化Markdown生成
4. トピックを絞らず、全情報を含める
5. NotebookLMがポッドキャストを生成しやすいように、会話調で構造化する

出力形式:
# {datetime.now().strftime("%Y年%m月%d日")} Telegramメッセージ整理

## 📊 概要
- 処理メッセージ数: {len(messages)}件
- データソース: Telegram
- 収集日時: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## テーマ別整理

（以下、自動抽出されたテーマごとに整理してください）

### テーマ1: [自動抽出されたテーマ名]

[該当するメッセージの内容を整理して記述]
[送信者や時刻などのメタデータも含める]
[会話の流れや文脈を保持する]

### テーマ2: [自動抽出されたテーマ名]

...

---

## 入力メッセージ一覧:

{all_messages}

---

上記のメッセージを分析し、意味のあるテーマに自動分類して、構造化されたMarkdownを生成してください。
テーマの数に制限はありません。全ての情報を漏らさず整理してください。
"""

        return prompt

    def _create_empty_document(self) -> str:
        """
        Create an empty document when no messages are provided.

        Returns:
            Markdown string for empty document
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        return f"""# {today} Telegramメッセージ整理

## 📊 概要
- 処理メッセージ数: 0件
- データソース: Telegram
- 収集日時: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## メッセージなし

本日は処理対象のメッセージがありませんでした。
"""

    def _create_fallback_document(self, messages: List[Dict]) -> str:
        """
        Create a fallback document when Gemini API fails.

        Args:
            messages: List of message dictionaries

        Returns:
            Simple Markdown document with all messages
        """
        today = datetime.now().strftime("%Y年%m月%d日")

        doc = f"""# {today} Telegramメッセージ整理

## 📊 概要
- 処理メッセージ数: {len(messages)}件
- データソース: Telegram
- 収集日時: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- 注意: AI整理に失敗したため、生データを記録しています

## メッセージ一覧

"""

        for i, msg in enumerate(messages, 1):
            chat_name = msg.get("chat_name", "Unknown")
            sender = msg.get("sender", "Unknown")
            date = msg.get("date", "")
            text = msg.get("text", "")

            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = date

            doc += f"### メッセージ {i}\n\n"
            doc += f"- **日時**: {formatted_date}\n"
            doc += f"- **チャット**: {chat_name}\n"
            doc += f"- **送信者**: {sender}\n\n"
            doc += f"{text}\n\n"
            doc += "---\n\n"

        return doc
