import math

from .graph import LinkGraph


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_privileged_pairs(
    graph: LinkGraph,
    embeddings: dict[str, list[float]],
    max_hops: int = 2,
    cosine_threshold: float = 0.6,
) -> list[tuple[str, str, float]]:
    """グラフ距離近い × 意味的距離遠い のノード対を返す（gap_score降順）"""
    results: list[tuple[str, str, float]] = []
    for a, b in graph.pairs_within_hops(max_hops=max_hops):
        emb_a = embeddings.get(a)
        emb_b = embeddings.get(b)
        if emb_a is None or emb_b is None:
            continue
        sim = cosine_similarity(emb_a, emb_b)
        if sim < cosine_threshold:
            gap_score = cosine_threshold - sim
            results.append((a, b, gap_score))
    results.sort(key=lambda x: x[2], reverse=True)
    return results
