from __future__ import annotations

import math

from .index import RAGIndex


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """2つのベクトルのコサイン類似度を返す（numpy不使用）。"""
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom


def search(
    index: RAGIndex,
    query_embedding: list[float],
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    インデックス内の全ページを対象にコサイン類似度で検索する。

    Returns:
        (page_id, similarity) のリスト（降順、最大 top_k 件）
    """
    all_embeddings = index.get_all_embeddings()

    scored: list[tuple[str, float]] = []
    for page_id, page_embedding in all_embeddings.items():
        sim = cosine_similarity(query_embedding, page_embedding)
        scored.append((page_id, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
