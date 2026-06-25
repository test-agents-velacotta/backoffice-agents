import os
from datetime import date, timedelta
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def generate_invoice(
    client_name: str,
    amount: int,
    description: str,
    invoice_number: str = None,
    output_dir: str = "output",
) -> str:
    """請求書PDFを生成してパスを返す"""
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    Path(output_dir).mkdir(exist_ok=True)
    today = date.today()
    due_date = today + timedelta(days=30)
    inv_num = invoice_number or f"INV-{today.strftime('%Y%m%d')}-001"
    filename = f"{output_dir}/{inv_num}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4

    c.setFont("HeiseiMin-W3", 20)
    c.drawString(20 * mm, h - 25 * mm, "請　求　書")

    c.setFont("HeiseiMin-W3", 10)
    c.drawString(20 * mm, h - 40 * mm, f"請求番号：{inv_num}")
    c.drawString(20 * mm, h - 47 * mm, f"請求日：{today.strftime('%Y年%m月%d日')}")
    c.drawString(20 * mm, h - 54 * mm, f"支払期限：{due_date.strftime('%Y年%m月%d日')}")

    c.setFont("HeiseiMin-W3", 12)
    c.drawString(20 * mm, h - 70 * mm, f"{client_name}　御中")

    tax = int(amount * 0.1)
    total = amount + tax

    c.setFont("HeiseiMin-W3", 14)
    c.drawString(20 * mm, h - 90 * mm, f"ご請求金額（税込）：¥{total:,}")

    c.setFont("HeiseiMin-W3", 10)
    c.drawString(20 * mm, h - 110 * mm, "【内訳】")
    c.drawString(25 * mm, h - 118 * mm, f"{description}")
    c.drawString(130 * mm, h - 118 * mm, f"¥{amount:,}")
    c.drawString(25 * mm, h - 126 * mm, "消費税（10%）")
    c.drawString(130 * mm, h - 126 * mm, f"¥{tax:,}")
    c.line(20 * mm, h - 130 * mm, 190 * mm, h - 130 * mm)
    c.drawString(25 * mm, h - 138 * mm, "合計")
    c.drawString(130 * mm, h - 138 * mm, f"¥{total:,}")

    issuer_name = os.getenv("ISSUER_NAME", "velacotta")
    issuer_email = os.getenv("ISSUER_EMAIL", "")
    c.setFont("HeiseiMin-W3", 10)
    c.drawString(20 * mm, h - 160 * mm, "【振込先】")
    c.drawString(25 * mm, h - 168 * mm, os.getenv("BANK_INFO", "（.envにBANK_INFOを設定してください）"))
    c.drawString(20 * mm, h - 185 * mm, f"発行者：{issuer_name}　{issuer_email}")

    c.save()
    return filename
