"""エージェント動作確認テスト（モック使用）"""

import json
import os
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


class TestEmailAgent(unittest.TestCase):
    def setUp(self):
        os.environ.pop("GMAIL_ALLOWED_SENDERS", None)
        os.environ.pop("GMAIL_LABEL", None)

    def test_requires_sender_or_label_filter(self):
        from agents.email_agent import run
        result = run(MagicMock(), label=None, senders=None)
        self.assertIn("絞り込み", result)

    @patch("agents.email_agent.gmail_client")
    def test_dry_run_does_not_create_draft(self, mock_gmail):
        from agents.email_agent import run

        mock_gmail.build_query.return_value = "is:unread from:(a@example.com)"
        mock_gmail.list_unread_messages.return_value = [{"id": "msg1"}]
        mock_gmail.get_message.return_value = {
            "id": "msg1",
            "thread_id": "t1",
            "sender": "a@example.com",
            "subject": "テスト件名",
            "body": "本文テスト",
            "message_id_header": "<abc@example.com>",
            "references": "",
        }

        client = MagicMock()
        msg = MagicMock()
        msg.content = [MagicMock(text="返信文のドラフトです")]
        client.messages.create.return_value = msg

        result = run(client, senders=["a@example.com"], dry_run=True)

        self.assertIn("DRY RUN", result)
        mock_gmail.create_draft_reply.assert_not_called()

    @patch("agents.email_agent._save_processed")
    @patch("agents.email_agent._load_processed", return_value=set())
    @patch("agents.email_agent.gmail_client")
    def test_creates_draft_and_records_processed_id(self, mock_gmail, mock_load, mock_save):
        from agents.email_agent import run

        mock_gmail.build_query.return_value = "is:unread from:(a@example.com)"
        mock_gmail.list_unread_messages.return_value = [{"id": "msg1"}]
        mock_gmail.get_message.return_value = {
            "id": "msg1",
            "thread_id": "t1",
            "sender": "a@example.com",
            "subject": "テスト件名",
            "body": "本文テスト",
            "message_id_header": "<abc@example.com>",
            "references": "",
        }
        mock_gmail.create_draft_reply.return_value = {"id": "draft1"}

        client = MagicMock()
        msg = MagicMock()
        msg.content = [MagicMock(text="返信文のドラフトです")]
        client.messages.create.return_value = msg

        result = run(client, senders=["a@example.com"], dry_run=False)

        mock_gmail.create_draft_reply.assert_called_once()
        mock_save.assert_called_once_with({"msg1"})
        self.assertIn("draft1", result)


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
