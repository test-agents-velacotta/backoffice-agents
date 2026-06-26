import os
from datetime import date
from pathlib import Path


VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "/Users/miho/Obsidian Vault"))
RESEARCH_DIR = VAULT_PATH / "Resources" / "Research"


def save_research(title: str, content: str, source_urls: list[str] = None) -> str:
    """リサーチ結果をObsidianのMarkdownファイルに保存する。ファイルパスを返す。"""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    safe_title = title.replace("/", "_").replace(":", "_")[:50]
    filename = f"{today} {safe_title}.md"
    filepath = RESEARCH_DIR / filename

    urls_section = "
".join(f"- {u}" for u in (source_urls or []))
    md = f"""---
title: "{title}"
date: {today}
tags: [research, agent]
---

{content}

## 参照URL

{urls_section}
"""
    filepath.write_text(md, encoding="utf-8")
    return str(filepath)
