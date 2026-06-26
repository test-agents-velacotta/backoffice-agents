import os
import anthropic
from tools.web_search import search_web
from tools.notion_writer import save_research as notion_save
from tools.obsidian_writer import save_research as obsidian_save


def _is_ci() -> bool:
    return os.getenv("CI") == "true"


def run(
    client: anthropic.Anthropic,
    query: str,
    save_to_notion: bool = True,
    save_to_obsidian: bool = True,
) -> str:
    """Web検索してリサーチ結果を要約し、NotionとObsidianに保存する"""
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
    title = f"リサーチ：{query}"
    saved_to = []

    if save_to_notion:
        page_url = notion_save(title=title, content=summary, source_urls=source_urls)
        saved_to.append(f"Notion: {page_url}")

    if save_to_obsidian and not _is_ci():
        filepath = obsidian_save(title=title, content=summary, source_urls=source_urls)
        saved_to.append(f"Obsidian: {filepath}")

    if saved_to:
        locations = "\n".join(f"📝 {s}" for s in saved_to)
        return f"{summary}\n\n{locations}"

    return summary
