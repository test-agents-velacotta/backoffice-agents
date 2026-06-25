import os
from datetime import date
from notion_client import Client


def get_client() -> Client:
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        raise ValueError("NOTION_API_KEY が設定されていません")
    return Client(auth=api_key)


def save_research(title: str, content: str, source_urls: list[str] = None) -> str:
    """リサーチ結果をNotionデータベースに保存する。ページURLを返す。"""
    client = get_client()
    db_id = os.getenv("NOTION_RESEARCH_DB_ID")
    if not db_id:
        raise ValueError("NOTION_RESEARCH_DB_ID が設定されていません")

    sources_text = "\n".join(source_urls or [])
    page = client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "日付": {"date": {"start": date.today().isoformat()}},
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": content}}]},
            },
            *(
                [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": f"【参照URL】\n{sources_text}"}}]
                        },
                    }
                ]
                if sources_text
                else []
            ),
        ],
    )
    return page["url"]
