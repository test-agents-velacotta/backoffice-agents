import anthropic
from agents import research_agent, content_agent, admin_agent


ROUTING_SYSTEM = """
あなたはバックオフィス自動化システムの司令塔です。
ユーザーの指示を受けて、実行すべきタスクと必要なパラメータをJSON形式で返してください。

利用可能なタスク：
- research: Web検索とリサーチ。パラメータ: {"query": "検索キーワード"}
- content: コンテンツ生成。パラメータ: {"content_type": "note|threads|proposal|email", "topic": "テーマ", "context": "追加情報（任意）"}
- invoice: 請求書生成。パラメータ: {"client_name": "会社名", "amount": 金額(税抜き), "description": "内容", "invoice_number": "番号（任意）"}
- minutes: 議事録整形。パラメータ: {"raw_text": "整形前テキスト"}

複数タスクが必要な場合は配列で返してください。

例：
{"tasks": [{"type": "research", "params": {"query": "AI導入 中小企業"}}, {"type": "content", "params": {"content_type": "note", "topic": "AI導入の第一歩"}}]}
"""


def route(client: anthropic.Anthropic, user_input: str) -> list[dict]:
    """ユーザー指示を解析してタスクリストを返す"""
    import json

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=ROUTING_SYSTEM,
        messages=[{"role": "user", "content": user_input}],
    )

    text = response.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end]).get("tasks", [])


def execute(client: anthropic.Anthropic, user_input: str) -> str:
    """ユーザー指示を受け取り、適切なエージェントを実行して結果を返す"""
    tasks = route(client, user_input)
    if not tasks:
        return "タスクを判断できませんでした。もう少し具体的に指示してください。"

    results = []
    for task in tasks:
        task_type = task.get("type")
        params = task.get("params", {})

        if task_type == "research":
            result = research_agent.run(client, **params)
        elif task_type == "content":
            result = content_agent.run(client, **params)
        elif task_type == "invoice":
            result = admin_agent.run_invoice(**params)
        elif task_type == "minutes":
            result = admin_agent.run_minutes(client, **params)
        else:
            result = f"未知のタスク: {task_type}"

        results.append(f"【{task_type}】\n{result}")

    return "\n\n---\n\n".join(results)
