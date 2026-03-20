from dataclasses import dataclass


@dataclass
class Node:
    id: str
    created: int
    updated: int
    link_count: int
    text_length: int


@dataclass
class Edge:
    source: str
    target: str
    type: str  # "direct" or "co-link"
