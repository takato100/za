import json
import sqlite3
from datetime import datetime, timezone

from .graph import LinkGraph
from .models import Edge, Node


class GraphStorage:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_snapshot (
                    id INTEGER PRIMARY KEY,
                    created_at TEXT,
                    nodes_json TEXT,
                    edges_json TEXT
                )
                """
            )

    def save(self, graph: LinkGraph) -> None:
        nodes_json = json.dumps(
            [
                {
                    "id": n,
                    "created": d.get("created"),
                    "updated": d.get("updated"),
                    "link_count": d.get("link_count"),
                    "text_length": d.get("text_length"),
                }
                for n, d in graph._g.nodes(data=True)
            ]
        )
        edges_json = json.dumps(
            [
                {"source": u, "target": v, "type": d.get("type")}
                for u, v, d in graph._g.edges(data=True)
            ]
        )
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO graph_snapshot (created_at, nodes_json, edges_json) VALUES (?, ?, ?)",
                (created_at, nodes_json, edges_json),
            )

    def load(self) -> LinkGraph:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT nodes_json, edges_json FROM graph_snapshot ORDER BY id DESC LIMIT 1"
            ).fetchone()

        graph = LinkGraph()
        if row is None:
            return graph

        nodes_data: list[dict] = json.loads(row[0])
        edges_data: list[dict] = json.loads(row[1])

        for n in nodes_data:
            graph.add_node(
                Node(
                    id=n["id"],
                    created=n.get("created") or 0,
                    updated=n.get("updated") or 0,
                    link_count=n.get("link_count") or 0,
                    text_length=n.get("text_length") or 0,
                )
            )
        for e in edges_data:
            graph.add_edge(Edge(source=e["source"], target=e["target"], type=e.get("type") or "direct"))

        return graph
