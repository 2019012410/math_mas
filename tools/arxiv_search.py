from __future__ import annotations

from typing import List


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arXiv and return a compact text summary."""
    try:
        import arxiv
    except ImportError as exc:
        raise RuntimeError("Package 'arxiv' is required. Install dependencies first.") from exc

    search = arxiv.Search(query=query, max_results=max_results)
    rows: List[str] = []
    for idx, item in enumerate(search.results(), start=1):
        rows.append(
            "\n".join(
                [
                    f"[{idx}] 标题: {item.title}",
                    f"摘要: {item.summary[:320].strip()}...",
                    f"链接: {item.entry_id}",
                ]
            )
        )
    return "\n\n".join(rows) if rows else "未找到相关文献。"
