"""Scrapbox data models."""
from dataclasses import dataclass, field


@dataclass
class ScrapboxPage:
    id: str
    title: str
    created: int        # unix timestamp
    updated: int
    links: list[str]    # リンク先ページタイトルのリスト
    image_urls: list[str]
    external_urls: list[str]
    text: str           # ページ本文（プレーンテキスト）
    line_count: int


@dataclass
class SyncState:
    project: str
    last_synced: int    # unix timestamp
    page_count: int
    errors: list[str] = field(default_factory=list)
