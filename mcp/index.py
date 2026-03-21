import json
import pickle
import random
from typing import Optional

import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer

from config import INDEX_DIR, EMBED_MODEL

_model: Optional[SentenceTransformer] = None
_graph: Optional[nx.DiGraph] = None
_embeddings: Optional[np.ndarray] = None
_titles: Optional[list] = None
_pages: Optional[dict] = None  # title -> page dict


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def build_index(pages: list[dict]) -> None:
    """Build graph + embeddings from fetched pages and save to INDEX_DIR."""
    G = nx.DiGraph()
    for p in pages:
        title = p["title"]
        G.add_node(title)
        for link in p.get("links", []):
            G.add_edge(title, link)

    titles = [p["title"] for p in pages]
    texts = [
        "{}\n{}".format(p["title"], "\n".join(p.get("descriptions", [])))
        for p in pages
    ]

    print(f"Embedding {len(texts)} pages...")
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    with open(INDEX_DIR / "pages.json", "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    with open(INDEX_DIR / "graph.pkl", "wb") as f:
        pickle.dump(G, f)
    np.save(INDEX_DIR / "embeddings.npy", embeddings.astype(np.float32))
    with open(INDEX_DIR / "titles.json", "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False)

    # Invalidate in-memory cache
    global _graph, _embeddings, _titles, _pages
    _graph = _embeddings = _titles = _pages = None


def _load() -> None:
    global _graph, _embeddings, _titles, _pages
    if _graph is not None:
        return

    pages_path = INDEX_DIR / "pages.json"
    if not pages_path.exists():
        raise FileNotFoundError(
            "Index not built yet. Call scrapbox_rebuild_index first."
        )

    with open(INDEX_DIR / "graph.pkl", "rb") as f:
        _graph = pickle.load(f)
    _embeddings = np.load(INDEX_DIR / "embeddings.npy")
    with open(INDEX_DIR / "titles.json", encoding="utf-8") as f:
        _titles = json.load(f)
    with open(INDEX_DIR / "pages.json", encoding="utf-8") as f:
        raw = json.load(f)
        _pages = {p["title"]: p for p in raw}


def search(query: str, limit: int = 5) -> list[tuple[str, float]]:
    """Semantic search by embedding similarity. Returns (title, score) pairs."""
    _load()
    q_emb = _get_model().encode([query])[0]
    norms = np.linalg.norm(_embeddings, axis=1) * np.linalg.norm(q_emb)
    sims = np.dot(_embeddings, q_emb) / np.maximum(norms, 1e-8)
    top_idx = np.argsort(sims)[::-1][:limit]
    return [(_titles[i], float(sims[i])) for i in top_idx]


def hop(start: str, min_hops: int = 1, max_hops: int = 3) -> list[tuple[str, int]]:
    """
    Graph traversal from start page.
    min_hops=2 skips obvious neighbors; use for 付きすぎず離れすぎず discovery.
    Uses undirected traversal so both inbound and outbound links count.
    """
    _load()
    if start not in _graph:
        return []
    undirected = _graph.to_undirected()
    lengths = nx.single_source_shortest_path_length(undirected, start, cutoff=max_hops)
    return [
        (node, dist)
        for node, dist in lengths.items()
        if min_hops <= dist <= max_hops and node != start
    ]


def jump(start: str, limit: int = 8) -> list[tuple[str, int]]:
    """
    Find weakly-linked pages: share neighbors with start but are NOT directly linked.
    This is the '間のリンク' — familiar unfamiliarity, 本歌取りの距離感.
    Returns (title, shared_neighbor_count) pairs.
    """
    _load()
    if start not in _graph:
        return []
    undirected = _graph.to_undirected()
    direct = set(undirected.neighbors(start)) | {start}

    shared: dict[str, int] = {}
    for neighbor in undirected.neighbors(start):
        for candidate in undirected.neighbors(neighbor):
            if candidate not in direct:
                shared[candidate] = shared.get(candidate, 0) + 1

    return sorted(shared.items(), key=lambda x: -x[1])[:limit]


def surface(seed: Optional[str] = None) -> str:
    """
    Surface a page title. With seed: semantic search → hop away slightly.
    Without seed: random pick (no query, no optimization).
    """
    _load()
    if seed:
        results = search(seed, limit=1)
        if results:
            hops = hop(results[0][0], min_hops=1, max_hops=2)
            if hops:
                return random.choice([t for t, _ in hops[:10]])
    return random.choice(_titles)


def get_page_content(title: str) -> Optional[dict]:
    """Return stored page data (title, descriptions, links)."""
    _load()
    return _pages.get(title)
