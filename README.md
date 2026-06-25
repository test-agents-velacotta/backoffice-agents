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

GitHub Secrets に上記の環境変数を登録することで動作します。

## テスト

```bash
python -m pytest tests/
```
