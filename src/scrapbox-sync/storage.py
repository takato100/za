"""Scrapbox データの SQLite 永続化。"""
import json
import sqlite3
from datetime import datetime, timezone
from .models import ScrapboxPage, SyncState


class PageStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    title TEXT PRIMARY KEY,
                    page_id TEXT,
                    created INTEGER,
                    updated INTEGER,
                    links_json TEXT,
                    image_urls_json TEXT,
                    external_urls_json TEXT,
                    text TEXT,
                    line_count INTEGER,
                    synced_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    project TEXT PRIMARY KEY,
                    last_synced INTEGER,
                    page_count INTEGER,
                    errors_json TEXT
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def upsert_page(self, page: ScrapboxPage):
        synced_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pages
                (title, page_id, created, updated, links_json,
                 image_urls_json, external_urls_json, text, line_count, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page.title,
                page.id,
                page.created,
                page.updated,
                json.dumps(page.links, ensure_ascii=False),
                json.dumps(page.image_urls, ensure_ascii=False),
                json.dumps(page.external_urls, ensure_ascii=False),
                page.text,
                page.line_count,
                synced_at,
            ))

    def get_page(self, title: str) -> ScrapboxPage | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM pages WHERE title = ?", (title,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_page(row)

    def get_all_pages(self) -> list[ScrapboxPage]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM pages ORDER BY updated DESC").fetchall()
        return [self._row_to_page(r) for r in rows]

    def get_updated_since(self, since_ts: int) -> list[ScrapboxPage]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pages WHERE updated > ? ORDER BY updated DESC", (since_ts,)
            ).fetchall()
        return [self._row_to_page(r) for r in rows]

    def _row_to_page(self, row) -> ScrapboxPage:
        # row order: title, page_id, created, updated, links_json,
        #            image_urls_json, external_urls_json, text, line_count, synced_at
        return ScrapboxPage(
            title=row[0],
            id=row[1],
            created=row[2],
            updated=row[3],
            links=json.loads(row[4]),
            image_urls=json.loads(row[5]),
            external_urls=json.loads(row[6]),
            text=row[7],
            line_count=row[8],
        )

    def save_sync_state(self, state: SyncState):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_state
                (project, last_synced, page_count, errors_json)
                VALUES (?, ?, ?, ?)
            """, (
                state.project,
                state.last_synced,
                state.page_count,
                json.dumps(state.errors, ensure_ascii=False),
            ))

    def get_sync_state(self, project: str) -> SyncState | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM sync_state WHERE project = ?", (project,)
            ).fetchone()
        if row is None:
            return None
        return SyncState(
            project=row[0],
            last_synced=row[1],
            page_count=row[2],
            errors=json.loads(row[3]),
        )
