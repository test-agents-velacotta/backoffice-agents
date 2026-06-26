# backoffice-agents

AIコンサル起業のバックオフィス業務を自動化するマルチエージェントシステム。

## 構成エージェント

| エージェント | 役割 |
|------------|------|
| Orchestrator | 自然言語の指示を受け取り、適切なエージェントに振り分ける |
| Research Agent | Web検索＋要約＋Notionへの自動保存 |
| Content Agent | note記事・Threads投稿・提案書・営業メールの生成 |
| Admin Agent | 請求書PDF生成・議事録整形 |

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env を編集して各APIキーを設定
```

## 使い方

```bash
# 自然言語で指示（Orchestratorが自動でルーティング）
python main.py ask "〇〇社のAI導入事例を調べて提案書も作って"

# リサーチ
python main.py research --query "AI導入 中小企業 事例"

# コンテンツ生成
python main.py content --type note --topic "FAXをなくす最初のステップ"
python main.py content --type threads --topic "今日のAI活用Tip"
python main.py content --type proposal --topic "受注業務のAI自動化" --context "FAX受注が多い食品卸業者向け"

# 請求書生成
python main.py invoice --client "〇〇株式会社" --amount 150000 --desc "AIコンサルティング（2026年6月分）"

# メール返信ドラフト作成（Gmail下書きのみ作成。自動送信はしない）
python main.py email draft --senders "client-a@example.com" --dry-run   # まず内容確認
python main.py email draft --senders "client-a@example.com"            # Gmailに下書き作成
```

## 環境変数

`.env.example` を参照。以下のAPIキーが必要：

- `ANTHROPIC_API_KEY` — Claude API
- `NOTION_API_KEY` — Notion連携
- `NOTION_RESEARCH_DB_ID` — リサーチ保存先NotionデータベースID
- `BRAVE_SEARCH_API_KEY` — Web検索
- `GOOGLE_SERVICE_ACCOUNT_JSON` — Google Drive連携（Admin Agent）
- `ISSUER_NAME` / `ISSUER_EMAIL` / `BANK_INFO` — 請求書の発行者情報

## 自動化ワークフロー（GitHub Actions）

- **毎朝8時**：業界リサーチを自動実行 → Notionに保存
- **毎週月曜朝7時**：週次コンテンツ案を自動生成
- **10分おき（任意・要セットアップ）**：新着メールへの返信ドラフトをGmailに作成

GitHub Secrets に上記の環境変数を登録することで動作します。

## Gmail連携（メール返信ドラフトの自動作成）

新着メールを検知して**Gmailの下書きフォルダに返信文を自動作成**します。
**メールの自動送信は一切行いません**。必ず人間が下書きを確認・編集してから送信してください。

### 安全のための設計

- 送信権限（`gmail.send`）は要求しない。スコープは `gmail.readonly` と `gmail.compose`（下書きのみ）に限定
- `GMAIL_ALLOWED_SENDERS` または `GMAIL_LABEL` のいずれかを必ず設定する必要がある（未設定だと実行を拒否する仕様）。受信メール全件を無差別に処理しない
- 処理済みメールIDを `GMAIL_STATE_PATH`（既定: `gmail_state.json`）に記録し、同じメールへの重複ドラフト作成を防ぐ
- 認証トークン（`token.json`）や認証情報のJSONは `.gitignore` 対象で、Gitに含まれない

### セットアップ手順

1. **Google Cloud Console** でプロジェクトを作成し、Gmail APIを有効化する
2. **OAuth同意画面**を設定する（個人利用なら「テストユーザー」に自分のGmailアドレスを追加すればOK。外部公開審査は不要）
3. **OAuthクライアントID**を作成（種類: 「デスクトップアプリ」）し、JSONをダウンロード
4. `.env` の `GMAIL_CREDENTIALS_JSON` にダウンロードしたJSONのパスを設定
5. `GMAIL_ALLOWED_SENDERS`（対象送信者、カンマ区切り）または `GMAIL_LABEL`（対象ラベル）を設定
6. 初回認証を実行（ブラウザでGoogleアカウントへのログイン・許可が必要。**この操作は本人が行ってください**）
   ```bash
   python tools/gmail_auth_setup.py
   ```
   成功すると `GMAIL_TOKEN_PATH`（既定: `token.json`）が作成されます。
7. まず `--dry-run` で生成内容を確認してから、本番実行してください
   ```bash
   python main.py email draft --dry-run
   python main.py email draft
   ```

### 定期実行（GitHub Actionsでポーリング）

GitHub Actionsでcron実行する場合、`token.json` の中身（JSON文字列）を `GMAIL_TOKEN_JSON` というSecretとして登録し、
ワークフロー内でファイルに復元してから実行してください。リフレッシュトークンが含まれていれば、
ブラウザ操作なしで自動更新されます（`workflows/.github/workflows/email_draft_polling.yml` 参照、既定は無効化されています）。

## テスト

```bash
python -m pytest tests/
```
