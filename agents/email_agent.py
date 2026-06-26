"""新着メールに対する返信ドラフトをGmailに作成するエージェント。

安全のための設計方針：
- メールの自動送信は行わない。常にGmailの下書きとして保存し、人間の確認・編集・送信を前提とする。
- 送信者またはラベルによる絞り込みを必須とする（個人情報を含む全受信メールを無差別に処理しない）。
- 処理済みのメールIDをローカルに記録し、同じメールへの重複ドラフト作成を防ぐ。
"""

import json
import os

import anthropic

from tools import gmail_client

SYSTEM_PROMPT = (
    "あなたはビジネスメールの返信文を作成するアシスタントです。"
    "受信メールの内容を踏まえ、丁寧で簡潔な日本語の返信文（本文のみ、署名なし）を作成してください。"
    "この返信は下書きとして保存され、必ず人間が確認・編集してから送信されます。"
    "金額や日程などの確約、断定的な合意の表明は避け、不明な点は確認する姿勢で書いてください。"
)


def run(
    client: anthropic.Anthropic,
    label: str = None,
    senders: list[str] = None,
    max_results: int = 10,
    dry_run: bool = False,
) -> str:
    """対象の新着メールに返信ドラフトを作成する。dry_run=Trueの場合は下書きを作成せず内容のみ返す。"""
    senders = senders if senders is not None else _default_senders()
    label = label or os.getenv("GMAIL_LABEL")

    if not senders and not label:
        return (
            "送信者またはラベルによる絞り込みが設定されていません。"
            "個人情報保護のため、GMAIL_ALLOWED_SENDERS／GMAIL_LABEL（または --senders／--label）のいずれかを必ず指定してください。"
        )

    service = gmail_client.get_service()
    query = gmail_client.build_query(label=label, senders=senders)

    processed = _load_processed()
    messages = gmail_client.list_unread_messages(service, query=query, max_results=max_results)

    results = []
    for msg_ref in messages:
        if msg_ref["id"] in processed:
            continue

        message = gmail_client.get_message(service, msg_ref["id"])
        reply_text = _draft_reply(client, message)

        if dry_run:
            results.append(f"[DRY RUN] {message['sender']} / {message['subject']}\n{reply_text}")
        else:
            draft = gmail_client.create_draft_reply(service, message, reply_text)
            results.append(f"下書き作成：{message['sender']} / {message['subject']}（draft id: {draft['id']}）")
            processed.add(msg_ref["id"])

    if not dry_run and results:
        _save_processed(processed)

    if not results:
        return "対象の新着メールはありませんでした。"

    return "\n\n---\n\n".join(results)


def _draft_reply(client: anthropic.Anthropic, message: dict) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"差出人：{message['sender']}\n"
                    f"件名：{message['subject']}\n\n"
                    f"本文：\n{message['body']}\n\n"
                    "上記メールへの返信文を作成してください。"
                ),
            }
        ],
    )
    return response.content[0].text


def _default_senders() -> list[str]:
    raw = os.getenv("GMAIL_ALLOWED_SENDERS", "")
    return [s.strip() for s in raw.split(",") if s.strip()]


def _state_path() -> str:
    return os.getenv("GMAIL_STATE_PATH", "gmail_state.json")


def _load_processed() -> set[str]:
    path = _state_path()
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return set(json.load(f))


def _save_processed(ids: set[str]) -> None:
    with open(_state_path(), "w") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)
