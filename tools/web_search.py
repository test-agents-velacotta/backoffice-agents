import os
import requests


def search_web(query: str, count: int = 5) -> list[dict]:
    """Brave Search APIでWeb検索を実行する"""
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise ValueError("BRAVE_SEARCH_API_KEY が設定されていません")

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": count, "lang": "ja", "country": "JP"}

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    results = response.json().get("web", {}).get("results", [])
    return [
        {"title": r.get("title"), "url": r.get("url"), "description": r.get("description")}
        for r in results
    ]
