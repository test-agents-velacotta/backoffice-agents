import anthropic
from tools.web_search import search_web
from tools.notion_writer import save_research


def run(client: anthropic.Anthropic, query: str, save_to_notion: bool = True) -> str:
    """Web検索してリサーチ結果を要約し、Notionに保存する"""
    results = search_web(query, count=5)
    search_summary = "\n".join(
        f"- [{r['title']}]({r['url']})\n  {r['description']}" for r in results
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=(
            "あなたはAIコンサルタントのリサーチアシスタントです。"
            "Web検索結果をもとに、ビジネス視点で簡潔にまとめてください。"
            "・要点を箇条書きで3〜5点\n・業界トレンドや示唆\n・次のアクション案"
        ),
        messages=[
            {
                "role": "user",
                "content": f"以下の検索結果を分析してまとめてください。\n\n検索クエリ：{query}\n\n{search_summary}",
            }
        ],
    )

    summary = response.content[0].text
    source_urls = [r["url"] for r in results]

    if save_to_notion:
        page_url = save_research(
            title=f"リサーチ：{query}",
            content=summary,
            source_urls=source_urls,
        )
        return f"{summary}\n\n📝 Notionに保存しました：{page_url}"

    return summary
