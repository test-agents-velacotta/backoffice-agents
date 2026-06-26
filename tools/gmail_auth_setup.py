#!/usr/bin/env python3
"""
Gmail連携の初回セットアップ用スクリプト。

ローカル環境でこのスクリプトを一度だけ実行し、ブラウザでGoogleアカウントの
認可を行ってください（このスクリプトはAIエージェントからは実行しません。
個人のGmailへのアクセス許可は必ず本人が行う操作です）。

事前準備:
1. Google Cloud Consoleでプロジェクトを作成し、Gmail APIを有効化する
2. OAuth同意画面を設定する（テストユーザーとして自分のメールを追加でOK）
3. OAuthクライアントID（種類: デスクトップアプリ）を作成し、JSONをダウンロード
4. .env の GMAIL_CREDENTIALS_JSON にダウンロードしたJSONのパスを設定する

実行:
    python tools/gmail_auth_setup.py

成功すると GMAIL_TOKEN_PATH（デフォルト: token.json）に認証情報が保存されます。
このファイルは秘密情報なので、絶対にGitにコミットしないでください（.gitignore対象）。
"""

import os
import sys

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from tools.gmail_client import SCOPES

load_dotenv()


def main():
    credentials_path = os.getenv("GMAIL_CREDENTIALS_JSON")
    if not credentials_path or not os.path.exists(credentials_path):
        print(
            "エラー：GMAIL_CREDENTIALS_JSON が設定されていない、またはファイルが見つかりません。\n"
            "Google Cloud ConsoleでダウンロードしたOAuthクライアントのJSONパスを .env に設定してください。"
        )
        sys.exit(1)

    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"認証に成功しました。トークンを {token_path} に保存しました。")
    print("このファイルは個人情報に準ずる秘密情報です。Gitにコミットしないよう注意してください。")


if __name__ == "__main__":
    main()
