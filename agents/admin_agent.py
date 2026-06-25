import anthropic
from tools.invoice_generator import generate_invoice


def run_invoice(
    client_name: str,
    amount: int,
    description: str,
    invoice_number: str = None,
) -> str:
    """請求書PDFを生成してパスを返す"""
    path = generate_invoice(
        client_name=client_name,
        amount=amount,
        description=description,
        invoice_number=invoice_number,
    )
    return f"請求書を生成しました：{path}"


def run_minutes(client: anthropic.Anthropic, raw_text: str) -> str:
    """生テキストから議事録を整形する"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=(
            "あなたは議事録整形アシスタントです。"
            "以下のフォーマットで整形してください：\n"
            "【日時】\n【参加者】\n【議題】\n【決定事項】\n【TODO（担当・期限）】\n【次回予定】"
        ),
        messages=[{"role": "user", "content": f"以下を議事録に整形してください：\n\n{raw_text}"}],
    )
    return response.content[0].text
