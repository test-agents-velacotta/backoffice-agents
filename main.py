#!/usr/bin/env python3
"""バックオフィス自動化エージェント CLIエントリーポイント"""

import argparse
import os
import sys
from dotenv import load_dotenv
import anthropic

load_dotenv()


def check_env():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("エラー：ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)


def main():
    check_env()
    client = anthropic.Anthropic()

    parser = argparse.ArgumentParser(description="バックオフィス自動化エージェント")
    subparsers = parser.add_subparsers(dest="command")

    # ask: Orchestratorに自然言語で指示
    ask_parser = subparsers.add_parser("ask", help="自然言語でタスクを指示する")
    ask_parser.add_argument("input", help="指示内容（例：「〇〇社をリサーチして提案書を作成して」）")

    # research: リサーチ直接実行
    research_parser = subparsers.add_parser("research", help="Web検索＋リサーチ")
    research_parser.add_argument("--query", required=True, help="検索クエリ")
    research_parser.add_argument("--no-notion", action="store_true", help="Notionに保存しない")
    research_parser.add_argument("--no-obsidian", action="store_true", help="Obsidianに保存しない")

    # content: コンテンツ生成
    content_parser = subparsers.add_parser("content", help="コンテンツ生成")
    content_parser.add_argument(
        "--type", required=True, choices=["note", "threads", "x", "proposal", "email"],
        dest="content_type", help="コンテンツの種類"
    )
    content_parser.add_argument("--topic", required=True, help="テーマ")
    content_parser.add_argument("--context", default="", help="追加コンテキスト")
    content_parser.add_argument(
        "--provider", default="claude", choices=["claude", "openai"],
        help="使用するAIプロバイダー（デフォルト: claude）"
    )

    # invoice: 請求書生成
    invoice_parser = subparsers.add_parser("invoice", help="請求書PDF生成")
    invoice_parser.add_argument("--client", required=True, dest="client_name", help="クライアント名")
    invoice_parser.add_argument("--amount", required=True, type=int, help="金額（税抜き）")
    invoice_parser.add_argument("--desc", required=True, dest="description", help="業務内容")
    invoice_parser.add_argument("--number", default=None, dest="invoice_number", help="請求番号")

    # email: 新着メールへの返信ドラフト作成（Gmail下書きのみ、自動送信はしない）
    email_parser = subparsers.add_parser("email", help="新着メールに返信ドラフトを作成（Gmail）")
    email_parser.add_argument("action", choices=["draft"], help="実行アクション")
    email_parser.add_argument("--label", default=None, help="対象とするGmailラベル")
    email_parser.add_argument(
        "--senders", default=None, help="対象とする送信者メールアドレス（カンマ区切り）"
    )
    email_parser.add_argument("--max", type=int, default=10, dest="max_results", help="処理する最大件数")
    email_parser.add_argument(
        "--dry-run", action="store_true", help="Gmailに下書きを作成せず、生成内容のみ表示する"
    )

    args = parser.parse_args()

    if args.command == "ask":
        from agents.orchestrator import execute
        print(execute(client, args.input))

    elif args.command == "research":
        from agents.research_agent import run
        print(run(client, args.query, save_to_notion=not args.no_notion, save_to_obsidian=not args.no_obsidian))

    elif args.command == "content":
        from agents.content_agent import run
        print(run(client, args.content_type, args.topic, args.context, args.provider))

    elif args.command == "invoice":
        from agents.admin_agent import run_invoice
        print(run_invoice(args.client_name, args.amount, args.description, args.invoice_number))

    elif args.command == "email":
        from agents.email_agent import run as run_email
        senders = [s.strip() for s in args.senders.split(",")] if args.senders else None
        print(run_email(client, label=args.label, senders=senders, max_results=args.max_results, dry_run=args.dry_run))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
