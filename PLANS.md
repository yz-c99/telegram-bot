# Telegram to Google Docs Auto-Collector - 実行計画

## プロジェクト概要

**目的**: 毎日未読のTelegramメッセージを自動収集・整理してGoogle Docsに保存し、NotebookLMでポッドキャスト化してインプットする

**主要技術**:
- Python 3.8+
- Telethon (Telegram API)
- Gemini API (無料枠)
- Google Docs API

**コスト**: $0/月（完全無料）

---

## Milestone 1: プロジェクトセットアップ

**目標**: 基本的なプロジェクト構造を作成し、開発環境を整える

**スコープ**:
- ディレクトリ構造の作成
- 依存関係の定義
- セキュリティ設定（.gitignore）
- 環境変数テンプレート

**タスク**:
1. プロジェクトディレクトリ構造を作成
   ```bash
   mkdir -p config credentials src/{telegram_client,filters,ai_processor,document,storage,utils} scripts data/{telegram_session,markdown_backup} logs cron .claude
   touch src/__init__.py src/*/__init__.py config/__init__.py
   ```

2. requirements.txt を作成
   ```txt
   telethon==1.35.0
   google-auth==2.25.2
   google-auth-oauthlib==1.2.0
   google-api-python-client==2.110.0
   google-generativeai==0.3.0
   python-dotenv==1.0.0
   PyYAML==6.0.1
   pytz==2023.3
   python-dateutil==2.8.2
   colorlog==6.8.0
   ```

3. .gitignore を作成
   ```gitignore
   .env
   credentials/*.json
   credentials/*.pickle
   !credentials/.gitkeep
   data/telegram_session/*.session*
   data/*.db
   logs/*.log
   __pycache__/
   *.py[cod]
   venv/
   .venv/
   ```

4. .env.example を作成
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE_NUMBER=+81_your_phone
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_CREDENTIALS_PATH=./credentials/google_credentials.json
   TIMEZONE=Asia/Tokyo
   EXECUTION_TIME=09:00
   LOG_LEVEL=INFO
   ```

5. 依存関係をインストール
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

**成果物**:
- 完全なディレクトリ構造
- requirements.txt
- .gitignore
- .env.example

**検証**:
```bash
# ディレクトリ構造確認
ls -la src/
ls -la config/
ls -la credentials/

# 仮想環境確認
source venv/bin/activate
pip list | grep telethon
pip list | grep google
```

**想定時間**: 1時間

---

## Milestone 2: 設定管理モジュール

**目標**: YAMLとenvファイルから設定を読み込むシンプルなモジュールを実装

**スコープ**:
- 環境変数の読み込み
- YAMLファイルの読み込み
- 基本的なロギング設定

**タスク**:
1. config/target_chats.yaml を作成
   ```yaml
   target_chats:
     - chat_id: "example_channel"
       name: "サンプルチャット"
       enabled: true

   filters:
     min_message_length: 10
     exclude_patterns:
       - "^おはよう$"
       - "^ありがとう$"
       - "^了解$"
   ```

2. config/settings.py を実装
   - 環境変数読み込み（python-dotenv）
   - YAML読み込み（PyYAML）
   - シンプルな設定クラス

3. src/utils/logger.py を実装
   - 基本的なロギング設定（コード内で定義、YAMLファイル不要）
   - ファイルとコンソール出力

**成果物**:
- config/target_chats.yaml
- config/settings.py
- src/utils/logger.py

**検証**:
```bash
python -c "from config.settings import Settings; s = Settings(); print(s.telegram_api_id)"
python -c "from src.utils.logger import get_logger; logger = get_logger('test'); logger.info('Test')"
```

**想定時間**: 1時間

---

## Milestone 3: データベース（SQLite）モジュール

**目標**: message_id追跡と処理ログを記録するSQLiteデータベースを実装

**スコープ**:
- データベーススキーマ定義
- テーブル作成
- CRUD操作
- message_id管理機能

**タスク**:
1. src/storage/state_manager.py を実装
   - SQLite接続管理
   - スキーマ定義と自動作成
   ```sql
   CREATE TABLE IF NOT EXISTS chat_state (
       chat_id TEXT PRIMARY KEY,
       chat_name TEXT NOT NULL,
       last_message_id INTEGER NOT NULL,
       last_processed_date TEXT NOT NULL,
       created_at TEXT NOT NULL,
       updated_at TEXT NOT NULL
   );

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
   );
   ```

2. StateManager クラスを実装
   - `get_last_message_id(chat_id)`: 最後のmessage_id取得
   - `update_message_id(chat_id, message_id)`: message_id更新
   - `add_processing_log(...)`: 処理ログ追加
   - `get_processing_history(days=7)`: 処理履歴取得

**成果物**:
- src/storage/state_manager.py
- data/state.db（自動生成）

**検証**:
```bash
python -c "
from src.storage.state_manager import StateManager
db = StateManager()
db.update_message_id('test_chat', 12345)
print(db.get_last_message_id('test_chat'))
"
# 出力: 12345

# データベース確認
sqlite3 data/state.db "SELECT * FROM chat_state;"
```

**想定時間**: 1.5-2時間

---

## Milestone 4: Telegram収集モジュール

**目標**: Telegramからメッセージを取得し、既読マークを付ける機能を実装

**スコープ**:
- Telethonクライアント接続
- 認証フロー
- message_id追跡によるメッセージ取得
- 既読マーク機能（send_read_acknowledge）

**タスク**:
1. src/telegram_client/client.py を実装
   - TelegramClient クラス
   - 認証処理
   - セッション管理

2. src/telegram_client/message_fetcher.py を実装
   - `fetch_new_messages(chat_id, last_message_id)`: 新規メッセージ取得
   - message_id追跡ロジック
   - **初回実行時の処理**: last_message_idが存在しない場合、直近24時間のメッセージを取得
   - メタデータ抽出（送信者、時刻、チャット名）

3. src/telegram_client/message_reader.py を実装
   - `mark_as_read(chat, message_id)`: 既読マーク機能
   - `send_read_acknowledge()` の実装

4. scripts/setup_telegram.py を作成
   - 初回認証フロー
   - 電話番号入力
   - 認証コード入力
   - セッションファイル生成

**成果物**:
- src/telegram_client/client.py
- src/telegram_client/message_fetcher.py
- src/telegram_client/message_reader.py
- scripts/setup_telegram.py

**検証**:
```bash
# 初回認証
python scripts/setup_telegram.py

# テスト実行
python -c "
from src.telegram_client.client import TelegramClient
client = TelegramClient()
# 接続確認
"
```

**想定時間**: 2.5-3時間

---

## Milestone 5: フィルタリングモジュール

**目標**: 基本的なノイズメッセージを除去する機能を実装

**スコープ**:
- 短文フィルタ
- 基本パターンマッチング

**タスク**:
1. src/filters/content_filter.py を実装
   - `filter_messages(messages, config)`: 単一関数でシンプルに処理
   - 10文字未満の除去
   - 設定ファイルのパターンマッチング
   - システムメッセージ除去

**成果物**:
- src/filters/content_filter.py

**検証**:
```bash
python -c "from src.filters.content_filter import filter_messages; print('OK')"
```

**想定時間**: 0.5時間

---

## Milestone 6: Gemini AI処理モジュール

**目標**: Gemini APIを使ってメッセージをテーマ別に整理・構造化する機能を実装

**スコープ**:
- Gemini API統合
- プロンプト設計
- テーマ抽出・構造化
- Markdown生成

**重要制約**:
- 1日1回のAPI呼び出しのみ（無料枠20回/日を超えない）
- 全メッセージを1回のAPI呼び出しで処理

**タスク**:
1. src/ai_processor/gemini_client.py を実装
   - Gemini API クライアント初期化
   - API呼び出しラッパー
   - エラーハンドリング（レート制限対応）

2. src/ai_processor/content_organizer.py を実装
   - `organize_messages(messages)`: メッセージ整理
   - プロンプト設計:
     ```
     以下のTelegramメッセージをNotebookLMポッドキャスト用に整理してください。

     要件:
     1. 全メッセージをテーマごとに自動グループ化（数の制限なし）
     2. 各テーマ内で時系列または論理的に整理
     3. メタデータ付き構造化Markdown生成
     4. トピックを絞らず、全情報を含める

     出力形式:
     # [日付] Telegramメッセージ整理
     ## 📊 概要
     - 処理メッセージ数: X件
     - 抽出テーマ数: Y個

     ## テーマ1: [自動抽出されたテーマ名]
     [メッセージ内容を整理して記述]

     ## テーマ2: [自動抽出されたテーマ名]
     ...
     ```

3. レート制限管理
   - 1日の呼び出し回数をSQLiteで記録
   - 20回制限チェック
   - 超過時はエラー通知

**成果物**:
- src/ai_processor/gemini_client.py
- src/ai_processor/content_organizer.py

**検証**:
```bash
python -c "
from src.ai_processor.content_organizer import ContentOrganizer
organizer = ContentOrganizer()
messages = [...]  # テストメッセージ
result = organizer.organize_messages(messages)
print(result[:200])  # Markdown確認
"
```

**想定時間**: 2.5-3時間

---

## Milestone 7: ドキュメント生成モジュール

**目標**: MarkdownをGoogle Docsに変換してアップロードする機能を実装

**スコープ**:
- Markdown生成
- Google Docs API統合
- OAuth認証
- ドキュメント作成・アップロード

**タスク**:
1. src/document/markdown_builder.py を実装
   - `build_markdown(organized_content)`: Markdown生成
   - ファイル保存（data/markdown_backup/）

2. src/document/google_docs_client.py を実装
   - Google OAuth 2.0 認証
   - `create_document(title, content)`: ドキュメント作成
   - Markdown → Google Docs変換
   - フォーマット適用（見出し、箇条書き、強調）

3. scripts/setup_google.py を作成
   - 初回OAuth認証フロー
   - ブラウザ起動→ログイン
   - トークン保存（credentials/token.pickle）

**成果物**:
- src/document/markdown_builder.py
- src/document/google_docs_client.py
- scripts/setup_google.py

**検証**:
```bash
# 初回認証
python scripts/setup_google.py

# テスト実行
python -c "
from src.document.google_docs_client import GoogleDocsClient
client = GoogleDocsClient()
doc_id = client.create_document('テストドキュメント', '# 見出し\n本文')
print(f'Document ID: {doc_id}')
"
```

**想定時間**: 2-3時間

---

## Milestone 8: メイン統合モジュール

**目標**: 全モジュールを統合し、エンドツーエンドの処理フローを実装

**スコープ**:
- メイン処理フロー
- エラーハンドリング
- ログ記録
- 処理時間計測

**タスク**:
1. src/utils/error_handler.py を実装
   - カスタム例外クラス
   - リトライロジック
   - エラー通知

2. src/main.py を実装
   ```python
   def main():
       1. 設定読み込み
       2. ロガー初期化
       3. StateManager初期化
       4. Telegram接続
       5. 各チャットループ:
          a. 最後のmessage_id取得
          b. 新規メッセージ取得
          c. 既読マーク
          d. message_id更新
       6. フィルタリング
       7. Gemini API処理（テーマ整理）
       8. Markdown生成・保存
       9. Google Docs アップロード
       10. 処理ログ記録
       11. 完了通知
   ```

3. エラーハンドリング
   - Telegram接続エラー
   - API呼び出しエラー
   - ネットワークエラー
   - リトライロジック（最大3回）

4. コマンドライン引数
   ```bash
   python src/main.py           # 通常実行
   python src/main.py --test    # テストモード
   python src/main.py --dry-run # ドライラン
   ```

**成果物**:
- src/main.py
- src/utils/error_handler.py

**検証**:
```bash
# テスト実行
python src/main.py --test

# 本番実行
python src/main.py

# ログ確認
tail -f logs/app.log

# データベース確認
sqlite3 data/state.db "SELECT * FROM processing_log ORDER BY created_at DESC LIMIT 1;"
```

**想定時間**: 2時間

---

## Milestone 9: スケジューリング設定

**目標**: 毎朝9時に自動実行されるCron設定を実装

**スコープ**:
- Cronスクリプト作成
- 実行権限設定
- Cron登録
- ログローテーション

**タスク**:
1. cron/daily_job.sh を作成
   ```bash
   #!/bin/bash
   cd /home/user/test
   source venv/bin/activate
   python src/main.py >> logs/cron.log 2>&1
   ```

2. 実行権限付与
   ```bash
   chmod +x cron/daily_job.sh
   ```

3. Cron登録
   ```bash
   crontab -e
   # 追加:
   0 9 * * * /home/user/test/cron/daily_job.sh
   ```

4. ログローテーション設定（任意）
   - logrotate設定

**成果物**:
- cron/daily_job.sh
- Cron登録完了

**検証**:
```bash
# 手動実行テスト
./cron/daily_job.sh

# Cron設定確認
crontab -l

# ログ確認
tail -f logs/cron.log

# 翌日9:00以降にログ確認
ls -l logs/
```

**想定時間**: 0.5時間

---

## Milestone 10: テスト・ドキュメント

**目標**: テストスクリプトとドキュメントを整備

**スコープ**:
- 接続テストスクリプト
- README作成
- セットアップガイド
- トラブルシューティング

**タスク**:
1. scripts/test_connection.py を作成
   - Telegram接続テスト
   - Google Docs接続テスト
   - Gemini API接続テスト
   - データベーステスト

2. scripts/get_chat_ids.py を作成
   - 参加中のチャット・グループ・チャンネル一覧を表示
   - 各チャットのID（識別番号）を表示
   - 設定ファイル（config/target_chats.yaml）にコピー可能な形式で出力

3. README.md を作成
   - プロジェクト概要
   - 必要な前提条件
   - セットアップ手順
     1. API認証情報取得（Telegram, Gemini, Google）
     2. 環境変数設定
     3. 初回認証実行
     4. 対象チャット設定
     5. テスト実行
     6. Cron設定
   - 使用方法
   - トラブルシューティング
   - FAQ

4. ドキュメント作成
   - API取得ガイド（Telegram, Gemini, Google）
   - チャットID確認方法（scripts/get_chat_ids.py の使用方法）
   - エラー対処法

**成果物**:
- scripts/test_connection.py
- scripts/get_chat_ids.py
- README.md
- docs/（任意）

**検証**:
```bash
# 接続テスト
python scripts/test_connection.py

# チャットID確認
python scripts/get_chat_ids.py

# README確認
cat README.md
```

**想定時間**: 2時間

---

## 総想定時間

| マイルストーン | 時間 |
|--------------|------|
| 1. プロジェクトセットアップ | 1時間 |
| 2. 設定管理モジュール | 1時間 |
| 3. データベースモジュール | 1.5-2時間 |
| 4. Telegram収集モジュール | 2.5-3時間 |
| 5. フィルタリングモジュール | 0.5時間 |
| 6. Gemini AI処理モジュール | 2.5-3時間 |
| 7. ドキュメント生成モジュール | 2-3時間 |
| 8. メイン統合モジュール | 2時間 |
| 9. スケジューリング設定 | 0.5時間 |
| 10. テスト・ドキュメント | 2時間 |
| **合計** | **15.5-20時間** |

---

## 重要な注意事項

### コスト制約
- **絶対に守る**: Gemini API無料枠（20回/日）を超えない
- 1日1回のAPI呼び出しのみ
- 呼び出し回数をデータベースで記録・監視

### セキュリティ
- `.env` ファイルは絶対にGitにコミットしない
- `credentials/` ディレクトリは.gitignore対象
- Telegramセッションファイルも保護

### 既読マーク
- メッセージ取得後、必ず `send_read_acknowledge()` を呼び出す
- 各チャットごとに個別に既読マーク

### message_id追跡
- 各チャットの最後の`message_id`を必ずSQLiteに記録
- 次回実行時はこのIDから取得開始
- **初回実行時**: last_message_idが存在しない場合、直近24時間のメッセージを取得
- システム障害時は24時間前からフォールバック

### エラーハンドリング
- ネットワークエラー時は3回までリトライ
- 1つのチャットが失敗しても他のチャットは継続
- 全エラーをログに記録

---

## 成功の定義

### Milestone完了時の状態
1. ✅ Telegram APIからメッセージ取得可能
2. ✅ 取得後に自動的に既読マーク
3. ✅ message_idがSQLiteに正しく記録
4. ✅ Gemini APIで構造化Markdown生成
5. ✅ Google Docsに自動アップロード
6. ✅ 毎朝9時に自動実行
7. ✅ 全処理が$0/月で運用可能

### 最終確認項目
- [ ] `python src/main.py` が成功する
- [ ] Google Driveにドキュメントが作成される
- [ ] ドキュメント構造がNotebookLM向けに最適化されている
- [ ] Cronが正しく動作する（翌日確認）
- [ ] ログが正しく記録される
- [ ] エラー時も適切にハンドリングされる
- [ ] Gemini API無料枠を超えない

---

## 次のステップ

このPLANS.mdに従って、Milestone 1から順番に実装を進めます。各Milestoneごとに：

1. タスク実行
2. 成果物確認
3. 検証実行
4. 次のMilestoneへ

実装中は TodoWrite を使ってリアルタイムで進捗を管理します。
