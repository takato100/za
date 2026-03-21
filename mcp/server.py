"""
Scrapbox MCP server.

Tools:
  scrapbox_rebuild_index  — fetch from Scrapbox API and rebuild local index
  scrapbox_search         — semantic search
  scrapbox_hop            — link graph traversal (近傍探索)
  scrapbox_jump           — weak link discovery (間のリンク)
  scrapbox_surface        — random/seeded page surfacing
  scrapbox_page           — read stored page content
"""

from typing import Optional
from mcp.server.fastmcp import FastMCP

import fetcher
import index as idx

mcp = FastMCP("scrapbox")


@mcp.tool()
async def scrapbox_rebuild_index() -> str:
    """
    Fetch all pages from the Scrapbox project and rebuild the local index
    (link graph + embeddings). Takes a few minutes on first run due to
    model download and embedding computation.
    """
    pages = await fetcher.fetch_all_pages()
    idx.build_index(pages)
    return f"Index rebuilt: {len(pages)} pages."


@mcp.tool()
def scrapbox_search(query: str, limit: int = 5) -> str:
    """
    Search Scrapbox pages by semantic similarity to query.
    Returns top matching page titles with scores.
    """
    try:
        results = idx.search(query, limit=limit)
    except FileNotFoundError as e:
        return str(e)
    if not results:
        return "No results."
    return "\n".join(f"- {title} ({score:.3f})" for title, score in results)


@mcp.tool()
def scrapbox_hop(page_title: str, min_hops: int = 1, max_hops: int = 3) -> str:
    """
    Traverse the Scrapbox link graph from page_title.
    Returns pages reachable within [min_hops, max_hops] link steps.

    Tips:
    - min_hops=1, max_hops=1  : direct neighbors only
    - min_hops=2, max_hops=3  : skip obvious neighbors, find 付きすぎず離れすぎず range
    - Uses undirected traversal (both inbound and outbound links count)
    """
    try:
        results = idx.hop(page_title, min_hops=min_hops, max_hops=max_hops)
    except FileNotFoundError as e:
        return str(e)
    if not results:
        return f"No pages found from '{page_title}' at {min_hops}–{max_hops} hops."

    by_dist: dict[int, list[str]] = {}
    for title, dist in results:
        by_dist.setdefault(dist, []).append(title)

    lines = [f"From '{page_title}':"]
    for dist in sorted(by_dist):
        sample = by_dist[dist][:8]
        suffix = f" (+{len(by_dist[dist]) - 8} more)" if len(by_dist[dist]) > 8 else ""
        lines.append(f"  {dist} hop{'s' if dist > 1 else ''}: {', '.join(sample)}{suffix}")
    return "\n".join(lines)


@mcp.tool()
def scrapbox_jump(page_title: str, limit: int = 8) -> str:
    """
    Find weakly-linked pages: pages that share neighbors with page_title
    but are NOT directly linked to it.

    These represent 間のリンク — the 'familiar unfamiliar'. Pages that share
    your conceptual neighborhood without being explicitly connected.
    Useful for 本歌取り-style discovery.
    """
    try:
        results = idx.jump(page_title, limit=limit)
    except FileNotFoundError as e:
        return str(e)
    if not results:
        return f"No weak links found for '{page_title}'."

    lines = [f"Weak links from '{page_title}':"]
    lines += [f"  - {title} (shared: {count})" for title, count in results]
    return "\n".join(lines)


@mcp.tool()
def scrapbox_surface(seed: Optional[str] = None) -> str:
    """
    Surface a page from Scrapbox.
    - No seed: random pick (no optimization, no personalization).
    - With seed: semantic search toward seed, then hop 1-2 steps away.

    Returns page title + its stored descriptions.
    """
    try:
        title = idx.surface(seed=seed)
    except FileNotFoundError as e:
        return str(e)

    page = idx.get_page_content(title)
    if not page:
        return f"Surfaced: {title}"

    desc = "\n".join(page.get("descriptions", []))
    return f"[{title}]\n{desc}" if desc else f"[{title}]"


@mcp.tool()
def scrapbox_page(page_title: str) -> str:
    """
    Read stored content of a specific Scrapbox page.
    Returns title, descriptions (first few lines), and linked pages.
    """
    try:
        page = idx.get_page_content(page_title)
    except FileNotFoundError as e:
        return str(e)
    if not page:
        return f"Page '{page_title}' not found in index."

    desc = "\n".join(page.get("descriptions", []))
    links = ", ".join(page.get("links", [])[:10])
    parts = [f"[{page_title}]"]
    if desc:
        parts.append(desc)
    if links:
        parts.append(f"Links: {links}")
    return "\n".join(parts)


if __name__ == "__main__":
    mcp.run()
