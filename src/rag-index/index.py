from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .chunker import chunk_text

try:
    import openai as _openai_module
    _OPENAI_AVAILABLE = True
except ImportError:
    _openai_module = None  # type: ignore[assignment]
    _OPENAI_AVAILABLE = False

_EMBEDDING_DIM = 1536
_EMBEDDING_MODEL = "text-embedding-3-small"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    page_id TEXT,
    chunk_index INTEGER,
    text TEXT,
    embedding_json TEXT,
    created_at TEXT
)
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chunks_page_id ON chunks (page_id)
"""


def _zero_vector() -> list[float]:
    return [0.0] * _EMBEDDING_DIM


class RAGIndex:
    def __init__(self, db_path: str, api_key: str | None = None) -> None:
        """
        db_path: SQLiteデータベースのパス
        api_key: OpenAI APIキー。Noneの場合は環境変数 OPENAI_API_KEY を使用。
                 どちらも無い場合はスタブ（ゼロベクトル）を使う。
        """
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._use_stub = not _OPENAI_AVAILABLE or not resolved_key

        if not self._use_stub and _OPENAI_AVAILABLE:
            self._client = _openai_module.OpenAI(api_key=resolved_key)
        else:
            self._client = None

        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute(_CREATE_TABLE_SQL)
            self._conn.execute(_CREATE_INDEX_SQL)

    def _embed(self, text: str) -> list[float]:
        """テキストのembeddingを取得する。スタブ時はゼロベクトルを返す。"""
        if self._use_stub or self._client is None:
            return _zero_vector()
        try:
            response = self._client.embeddings.create(
                model=_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            return _zero_vector()

    def add_page(self, page_id: str, text: str) -> None:
        """ページテキストをチャンク化し、embeddingを生成してSQLiteに保存する。"""
        chunks = chunk_text(page_id, text)
        now = datetime.now(timezone.utc).isoformat()

        with self._conn:
            # 既存のチャンクを削除（upsert代わり）
            self._conn.execute("DELETE FROM chunks WHERE page_id = ?", (page_id,))

            for chunk in chunks:
                embedding = self._embed(chunk.text)
                self._conn.execute(
                    """
                    INSERT INTO chunks
                        (id, page_id, chunk_index, text, embedding_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        chunk.page_id,
                        chunk.chunk_index,
                        chunk.text,
                        json.dumps(embedding),
                        now,
                    ),
                )

    def get_embedding(self, page_id: str) -> list[float] | None:
        """ページの代表ベクトル（チャンクのembeddingの平均）を返す。"""
        rows = self._conn.execute(
            "SELECT embedding_json FROM chunks WHERE page_id = ? ORDER BY chunk_index",
            (page_id,),
        ).fetchall()

        if not rows:
            return None

        embeddings = [json.loads(row["embedding_json"]) for row in rows]
        return _mean_vectors(embeddings)

    def get_all_embeddings(self) -> dict[str, list[float]]:
        """page_id -> 代表ベクトル の辞書を返す。"""
        rows = self._conn.execute(
            "SELECT page_id, embedding_json FROM chunks ORDER BY page_id, chunk_index"
        ).fetchall()

        # page_id ごとにembeddingを集約
        page_embeddings: dict[str, list[list[float]]] = {}
        for row in rows:
            pid = row["page_id"]
            emb = json.loads(row["embedding_json"])
            page_embeddings.setdefault(pid, []).append(emb)

        return {
            pid: _mean_vectors(embs)
            for pid, embs in page_embeddings.items()
        }

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "RAGIndex":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _mean_vectors(vectors: list[list[float]]) -> list[float]:
    """複数のベクトルの要素ごと平均を計算する（numpy不使用）。"""
    if not vectors:
        return _zero_vector()
    n = len(vectors)
    dim = len(vectors[0])
    result = [0.0] * dim
    for vec in vectors:
        for i, v in enumerate(vec):
            result[i] += v
    return [x / n for x in result]
