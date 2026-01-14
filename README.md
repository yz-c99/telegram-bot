# Telegram to Google Docs Auto-Collector

毎日未読のTelegramメッセージを自動収集・整理してGoogle Docsに保存し、NotebookLMでポッドキャスト化するシステム

## 概要

- **自動収集**: 毎朝9時に指定したTelegramチャットから未読メッセージを自動取得
- **AI整理**: Gemini APIでメッセージをテーマ別に構造化
- **自動保存**: Google Docsに自動アップロード（NotebookLM用に最適化）
- **既読マーク**: 取得後に自動的にメッセージを既読にする
- **完全無料**: 月額$0で運用（全て無料枠内）

## 必要な前提条件

### API認証情報

1. **Telegram API**
   - API ID と API Hash を取得: https://my.telegram.org/apps
   - 電話番号

2. **Gemini API**
   - API Key を取得: https://makersuite.google.com/app/apikey
   - 無料枠: 20リクエスト/日

3. **Google Docs API**
   - OAuth 2.0 認証情報を取得: https://console.cloud.google.com/
   - Google Docs API を有効化
   - credentials.json をダウンロード

### システム要件

- Python 3.8以上
- Linux環境（Cronスケジューリング用）

## セットアップ手順

### 1. プロジェクトのクローンと依存関係インストール

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .env.example をコピー
cp .env.example .env

# .env を編集して認証情報を設定
nano .env
```

### 3. Telegram認証

```bash
python scripts/setup_telegram.py
```

電話番号と認証コードを入力してセッションを作成します。

### 4. Google Docs認証

```bash
# credentials.json を credentials/ に配置
cp /path/to/credentials.json credentials/google_credentials.json

# OAuth認証実行
python scripts/setup_google.py
```

ブラウザが開くのでGoogleアカウントでログインして許可します。

### 5. 対象チャット設定

```bash
# チャットIDを確認
python scripts/get_chat_ids.py

# config/target_chats.yaml を編集
nano config/target_chats.yaml
```

取得したいチャットのIDを設定します。

### 6. 接続テスト

```bash
python scripts/test_connection.py
```

全てのAPI接続が成功することを確認します。

### 7. テスト実行

```bash
# ドライラン（実際の変更なし）
python src/main.py --dry-run

# テストモード（Google Docs アップロードなし）
python src/main.py --test

# 本番実行
python src/main.py
```

### 8. Cron設定（自動実行）

```bash
# Cron編集
crontab -e

# 毎朝9時に実行（以下を追加）
0 9 * * * /home/user/test/cron/daily_job.sh >> /home/user/test/logs/cron.log 2>&1
```

## 使用方法

### 手動実行

```bash
# 通常実行
python src/main.py

# テストモード（Google Docsスキップ）
python src/main.py --test

# ドライラン（読まない、状態更新しない）
python src/main.py --dry-run
```

### 自動実行

Cronで設定した時刻（デフォルト: 毎朝9時）に自動実行されます。

### NotebookLMでポッドキャスト化

1. Google Docsに保存されたドキュメントを確認
2. NotebookLM (https://notebooklm.google.com/) を開く
3. ドキュメントをアップロード
4. ポッドキャストを生成

## ディレクトリ構造

```
.
├── config/              # 設定ファイル
├── credentials/         # API認証情報
├── src/                 # ソースコード
├── scripts/             # セットアップスクリプト
├── data/                # データベース・セッション
├── logs/                # ログファイル
└── cron/                # Cronスクリプト
```

## トラブルシューティング

### Telegram接続エラー

```bash
# セッションファイル削除して再認証
rm data/telegram_session/*.session
python scripts/setup_telegram.py
```

### Gemini API制限エラー

無料枠（20リクエスト/日）を超えた場合は翌日まで待機してください。

### Google Docs認証エラー

```bash
# トークン削除して再認証
rm credentials/token.pickle
python scripts/setup_google.py
```

### ログ確認

```bash
# アプリケーションログ
tail -f logs/app.log

# Cron実行ログ
tail -f logs/cron.log

# データベース確認
sqlite3 data/state.db "SELECT * FROM processing_log ORDER BY created_at DESC LIMIT 5;"
```

## 重要な制約

- **月額コスト$0を維持**: 全て無料枠内で運用
- **Gemini API制限**: 1日1回の実行（20リクエスト/日を超えない）
- **既読マーク**: メッセージ取得後、自動的に既読マークが付きます
- **セキュリティ**: `.env`や`credentials/`は絶対にGitにコミットしない

## プロジェクト構成

- **技術スタック**: Python 3.8+, Telethon, Gemini API, Google Docs API
- **データベース**: SQLite（message_id追跡、処理ログ）
- **スケジューリング**: Cron
- **月額コスト**: $0（完全無料）

## ライセンス

MIT License
