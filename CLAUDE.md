# Telegram to Google Docs Auto-Collector

## プロジェクト概要

毎日未読のTelegramメッセージを自動収集・整理してGoogle Docsに保存し、NotebookLMでポッドキャスト化するシステム。

**技術スタック**: Python 3.8+, Telethon, Gemini API, Google Docs API
**月額コスト**: $0（完全無料運用が必須）

---

## 🚨 重要制約・ルール（絶対遵守）

### コスト制約
1. **月額コスト$0を維持すること（最優先事項）**
2. **Gemini API無料枠（20リクエスト/日）を絶対に超えないこと**
   - 1日1回のAPI呼び出しのみ許可
   - 呼び出し回数をSQLiteで記録・監視
   - 超過しそうな場合はエラーで停止
3. **Google Docs API、Telegram APIも無料枠内で運用**

### セキュリティ制約
1. **絶対に`.env`ファイルを読み取らないこと**
2. **絶対に`credentials/`ディレクトリを読み取らないこと**
3. **絶対にTelegramセッションファイルを直接操作しないこと**
4. **APIキーやパスワードをコード内にハードコーディングしないこと**
5. **機密情報を含むファイルは必ず.gitignoreに追加すること**

### 機能制約
1. **メッセージ取得後、必ず既読マーク（`send_read_acknowledge()`）を実行**
2. **message_idを必ずSQLiteに記録し、次回実行時に使用**
3. **Gemini APIは全メッセージを1回の呼び出しで処理（テーマ数に制限なし）**
4. **トピックを絞らず、全情報を整理・構造化すること**

### 変更禁止ファイル
- `.env`
- `credentials/*.json`
- `credentials/*.pickle`
- `data/telegram_session/*.session`

---

## アーキテクチャ

### システムフロー
```
Cron (9:00 AM)
  → Telegram収集（message_id追跡）
  → フィルタリング（ノイズ除去）
  → Gemini API（1回のみ・構造化）
  → Markdown生成
  → Google Docs アップロード
  → 状態更新（SQLite）
  → 【手動】NotebookLM
```

### ディレクトリ構造
```
src/
  telegram_client/  - Telegram API統合
  filters/          - メッセージフィルタリング
  ai_processor/     - Gemini API処理
  document/         - Markdown・Google Docs生成
  storage/          - SQLite状態管理
  utils/            - ロガー、エラーハンドラー
```

---

## 開発コマンド

### セットアップ
```bash
# 仮想環境作成・有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# Telegram初回認証
python scripts/setup_telegram.py

# Google初回認証
python scripts/setup_google.py

# 接続テスト
python scripts/test_connection.py
```

### 実行
```bash
# テスト実行
python src/main.py --test

# ドライラン（実際の処理なし）
python src/main.py --dry-run

# 本番実行
python src/main.py
```

### デバッグ
```bash
# ログ確認
tail -f logs/app.log

# データベース確認
sqlite3 data/state.db "SELECT * FROM chat_state;"
sqlite3 data/state.db "SELECT * FROM processing_log ORDER BY created_at DESC LIMIT 5;"

# Cron実行ログ
tail -f logs/cron.log
```

### Cron設定
```bash
# Cron編集
crontab -e

# 追加（毎朝9時実行）
0 9 * * * /home/user/test/cron/daily_job.sh >> /home/user/test/logs/cron.log 2>&1

# Cron確認
crontab -l
```

---

## コーディング規約

### Python スタイル
- PEP 8準拠
- 関数名: `snake_case`
- クラス名: `PascalCase`
- 定数: `UPPER_CASE`
- docstringは必須（主要な関数・クラス）

### インポート順序
```python
# 標準ライブラリ
import os
import sys

# サードパーティ
from telethon import TelegramClient
import google.generativeai as genai

# ローカル
from config.settings import Settings
from src.utils.logger import get_logger
```

### エラーハンドリング
```python
# カスタム例外を使用
from src.utils.error_handler import TelegramError, GeminiAPIError

try:
    # 処理
except TelegramError as e:
    logger.error(f"Telegram error: {e}")
    # リトライまたは通知
```

### ロギング
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

---

## 主要モジュールの責務

### `src/telegram_client/`
- Telegram APIとの通信
- メッセージ取得（message_id追跡）
- 既読マーク（`send_read_acknowledge()`）
- セッション管理

### `src/filters/`
- 短文除去（10文字未満）
- パターンマッチング（挨拶、相槌）
- スタンプ・システムメッセージ除去

### `src/ai_processor/`
- **Gemini API呼び出し（1日1回のみ）**
- 全メッセージをテーマ別に整理・構造化
- トピック数に制限なし
- NotebookLM最適化されたMarkdown生成

### `src/document/`
- Markdown生成・保存
- Google Docs APIとの通信
- Markdown → Google Docs変換
- フォーマット適用

### `src/storage/`
- SQLite操作
- message_id記録・取得
- 処理ログ保存

---

## 設定ファイル

### `.env`（機密情報）
```env
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_PHONE_NUMBER=...
GEMINI_API_KEY=...
GOOGLE_CREDENTIALS_PATH=...
```

### `config/target_chats.yaml`
```yaml
target_chats:
  - chat_id: "channel_username"
    name: "表示名"
    enabled: true

filters:
  min_message_length: 10
  exclude_patterns: ["^おはよう$", "^ありがとう$"]
```

---

## トラブルシューティング

### Telegram接続エラー
```bash
# セッションファイル削除して再認証
rm data/telegram_session/*.session
python scripts/setup_telegram.py
```

### Gemini API制限エラー
```bash
# 呼び出し回数確認
sqlite3 data/state.db "SELECT COUNT(*) FROM processing_log WHERE execution_date = date('now');"

# 20回を超えていたら翌日まで待機
```

### Google Docs認証エラー
```bash
# トークン削除して再認証
rm credentials/token.pickle
python scripts/setup_google.py
```

---

## テスト戦略

### 単体テスト
各モジュールは独立してテスト可能に設計

### 統合テスト
`scripts/test_connection.py`で全API接続を確認

### エンドツーエンドテスト
```bash
python src/main.py --test
```

---

## デプロイ・運用

### 初回デプロイ
1. API認証情報取得
2. `.env`設定
3. 初回認証実行
4. `config/target_chats.yaml`設定
5. テスト実行
6. Cron登録

### 日次運用
- **自動**: 毎朝9時にCron実行
- **手動**: Google Docs → NotebookLM アップロード

### モニタリング
- ログファイル監視（`logs/app.log`）
- データベース確認（処理履歴）
- ディスク容量チェック

---

## FAQ

**Q: Gemini API無料枠を超えたらどうなる？**
A: エラーで停止します。1日1回のAPI呼び出しを守ってください。

**Q: メッセージが多すぎる場合は？**
A: フィルタリング設定を調整するか、対象チャットを減らしてください。

**Q: NotebookLMへの自動アップロードは？**
A: 現在は手動です。将来的にEnterprise API統合を検討。

**Q: 既読マークをつけたくない場合は？**
A: 仕様上、既読マークは必須です（ユーザー要望）。

---

## 参考リンク

- [Telegram API Documentation](https://core.telegram.org/)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google Docs API Documentation](https://developers.google.com/docs/api)
- [NotebookLM](https://notebooklm.google.com/)

---

## プロジェクト目標

✅ 完全無料（$0/月）で運用
✅ 毎日自動実行
✅ 未読メッセージのみ取得（message_id追跡）
✅ 自動的に既読マーク
✅ AI による構造化（NotebookLM最適化）
✅ Google Docsに自動保存
✅ ポッドキャストでインプット
