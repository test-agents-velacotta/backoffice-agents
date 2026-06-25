"""エージェント動作確認テスト（モック使用）"""

import json
import unittest
from unittest.mock import MagicMock, patch


class TestOrchestrator(unittest.TestCase):
    def _make_client(self, response_text: str):
        client = MagicMock()
        msg = MagicMock()
        msg.content = [MagicMock(text=response_text)]
        client.messages.create.return_value = msg
        return client

    def test_route_research(self):
        from agents.orchestrator import route
        payload = '{"tasks": [{"type": "research", "params": {"query": "AI導入 中小企業"}}]}'
        client = self._make_client(payload)
        tasks = route(client, "AI導入について調べて")
        self.assertEqual(tasks[0]["type"], "research")
        self.assertIn("query", tasks[0]["params"])

    def test_route_invoice(self):
        from agents.orchestrator import route
        payload = '{"tasks": [{"type": "invoice", "params": {"client_name": "テスト株式会社", "amount": 100000, "description": "AIコンサルティング"}}]}'
        client = self._make_client(payload)
        tasks = route(client, "テスト株式会社に10万円の請求書を作って")
        self.assertEqual(tasks[0]["type"], "invoice")

    def test_route_multi_task(self):
        from agents.orchestrator import route
        payload = '{"tasks": [{"type": "research", "params": {"query": "テスト"}}, {"type": "content", "params": {"content_type": "note", "topic": "テスト"}}]}'
        client = self._make_client(payload)
        tasks = route(client, "テストについて調べてnote記事も書いて")
        self.assertEqual(len(tasks), 2)


class TestContentAgent(unittest.TestCase):
    def test_invalid_content_type(self):
        from agents.content_agent import run
        client = MagicMock()
        with self.assertRaises(ValueError):
            run(client, "invalid_type", "テスト")


class TestInvoiceGenerator(unittest.TestCase):
    @patch("tools.invoice_generator.canvas.Canvas")
    def test_generate_invoice(self, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        from tools.invoice_generator import generate_invoice
        path = generate_invoice("テスト株式会社", 100000, "AIコンサルティング")
        self.assertTrue(path.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
