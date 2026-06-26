"""Gmail APIラッパー。読み取りと下書き作成のみを行い、メールの自動送信は行わない。"""

import base64
import os
from email.mime.text import MIMEText
from email.utils import parseaddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# gmail.readonly: 受信メールの読み取り / gmail.compose: 下書きの作成のみ（送信権限は含まない）
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_service():
    """認証済みのGmail APIサービスを返す。未認証の場合はセットアップを促す。"""
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")

    if not os.path.exists(token_path):
        raise RuntimeError(
            "Gmail認証トークンが見つかりません。"
            "`python tools/gmail_auth_setup.py` を実行して初回認証（ブラウザでのログイン）を行ってください。"
        )

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError(
                "Gmail認証トークンが無効です。`python tools/gmail_auth_setup.py` を再実行してください。"
            )

    return build("gmail", "v1", credentials=creds)


def build_query(label: str = None, senders: list[str] = None) -> str:
    """未読メールに対する検索クエリを構築する。label/sendersでの絞り込みを必須として扱う想定。"""
    parts = ["is:unread"]
    if label:
        parts.append(f"label:{label}")
    if senders:
        senders_query = " OR ".join(senders)
        parts.append(f"from:({senders_query})")
    return " ".join(parts)


def list_unread_messages(service, query: str, max_results: int = 10) -> list[dict]:
    resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    return resp.get("messages", [])


def get_message(service, msg_id: str) -> dict:
    """メールの詳細を取得し、返信ドラフト作成に必要な情報を抽出する。"""
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

    return {
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "sender": headers.get("From", ""),
        "subject": headers.get("Subject", ""),
        "message_id_header": headers.get("Message-ID", ""),
        "references": headers.get("References", ""),
        "body": _extract_body(msg["payload"]),
    }


def _extract_body(payload: dict) -> str:
    """payloadからtext/plain本文を再帰的に抽出する。"""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_body(payload["body"]["data"])

    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text

    return ""


def _decode_body(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8", errors="replace")


def create_draft_reply(service, message: dict, reply_text: str) -> dict:
    """元メールへの返信を、Gmailの下書きとして作成する（送信はしない）。"""
    to_addr = parseaddr(message["sender"])[1]
    subject = message["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    mime_message = MIMEText(reply_text)
    mime_message["To"] = to_addr
    mime_message["Subject"] = subject
    if message.get("message_id_header"):
        mime_message["In-Reply-To"] = message["message_id_header"]
        mime_message["References"] = f"{message.get('references', '')} {message['message_id_header']}".strip()

    raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("UTF-8")

    return (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw, "threadId": message["thread_id"]}})
        .execute()
    )
