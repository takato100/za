import networkx as nx

from .models import Edge, Node


class LinkGraph:
    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    def add_node(self, node: Node) -> None:
        self._g.add_node(
            node.id,
            created=node.created,
            updated=node.updated,
            link_count=node.link_count,
            text_length=node.text_length,
        )

    def add_edge(self, edge: Edge) -> None:
        self._g.add_edge(edge.source, edge.target, type=edge.type)

    def neighbors_within_hops(self, node_id: str, max_hops: int = 2) -> list[str]:
        # BFS on undirected view to collect nodes reachable within max_hops
        undirected = self._g.to_undirected()
        visited: set[str] = set()
        frontier = {node_id}
        for _ in range(max_hops):
            next_frontier: set[str] = set()
            for n in frontier:
                for nb in undirected.neighbors(n):
                    if nb not in visited and nb != node_id:
                        next_frontier.add(nb)
            visited.update(frontier)
            frontier = next_frontier - visited
        visited.discard(node_id)
        return list(visited | frontier)

    def shortest_path_length(self, a: str, b: str) -> int:
        undirected = self._g.to_undirected()
        return nx.shortest_path_length(undirected, a, b)

    def pairs_within_hops(self, max_hops: int = 2) -> list[tuple[str, str]]:
        undirected = self._g.to_undirected()
        nodes = list(self._g.nodes)
        pairs: list[tuple[str, str]] = []
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                try:
                    if nx.shortest_path_length(undirected, a, b) <= max_hops:
                        pairs.append((a, b))
                except nx.NetworkXNoPath:
                    pass
        return pairs

    def build_co_links(self) -> None:
        # Add co-link edges between nodes that share at least one common direct neighbour
        undirected = self._g.to_undirected()
        nodes = list(self._g.nodes)
        for i, a in enumerate(nodes):
            neighbors_a = set(undirected.neighbors(a))
            for b in nodes[i + 1 :]:
                if a == b:
                    continue
                neighbors_b = set(undirected.neighbors(b))
                if neighbors_a & neighbors_b:
                    if not self._g.has_edge(a, b) and not self._g.has_edge(b, a):
                        self._g.add_edge(a, b, type="co-link")
