import anthropic


CONTENT_TYPES = {
    "note": "note記事（2000〜3000字、読者に価値を提供する実践的な内容）",
    "threads": "Threads投稿（500字以内、共感・保存されやすい投稿）",
    "proposal": "提案書（課題→解決策→費用→スケジュールの構成）",
    "email": "営業メール（件名付き、簡潔で行動を促す内容）",
}


def run(client: anthropic.Anthropic, content_type: str, topic: str, context: str = "") -> str:
    """指定タイプのコンテンツを生成する"""
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"content_type は {list(CONTENT_TYPES.keys())} のいずれかを指定してください")

    content_desc = CONTENT_TYPES[content_type]
    context_section = f"\n\n【追加コンテキスト】\n{context}" if context else ""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        system=(
            "あなたはAIコンサルタントのコンテンツ作成アシスタントです。"
            "ターゲットはAI未導入の中小企業経営者・担当者です。"
            "専門用語は避け、具体例を使って分かりやすく伝えてください。"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下のテーマで{content_desc}を作成してください。\n\n"
                    f"テーマ：{topic}{context_section}"
                ),
            }
        ],
    )

    return response.content[0].text
