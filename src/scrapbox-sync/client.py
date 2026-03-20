"""Scrapbox API client.

認証: Scrapbox の connect.sid Cookie を使用。
環境変数 SCRAPBOX_COOKIE または設定ファイルから読み込む。

T-01 解決前はパブリックプロジェクトのみ動作（認証不要）。
"""
import json
import os
import time
import urllib.request
import urllib.parse
from .models import ScrapboxPage


SCRAPBOX_API_BASE = "https://scrapbox.io/api"


class ScrapboxClient:
    def __init__(self, project: str, cookie: str | None = None):
        self.project = project
        # SCRAPBOX_COOKIE 環境変数 → 引数 の順で優先
        self.cookie = cookie or os.environ.get("SCRAPBOX_COOKIE", "")

    def _get(self, path: str) -> dict:
        url = f"{SCRAPBOX_API_BASE}{path}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        if self.cookie:
            req.add_header("Cookie", self.cookie)

        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def list_pages(self, limit: int = 100, skip: int = 0) -> dict:
        """ページ一覧を取得。レスポンスをそのまま返す。"""
        path = f"/pages/{urllib.parse.quote(self.project)}?limit={limit}&skip={skip}"
        return self._get(path)

    def get_page(self, title: str) -> ScrapboxPage:
        """ページ詳細を取得して ScrapboxPage に変換する。"""
        path = f"/pages/{urllib.parse.quote(self.project)}/{urllib.parse.quote(title)}"
        data = self._get(path)
        return self._parse_page(data)

    def _parse_page(self, data: dict) -> ScrapboxPage:
        lines = data.get("lines", [])
        text_lines = [line.get("text", "") for line in lines]
        text = "\n".join(text_lines)

        # リンクは Scrapbox API の links フィールドから取得
        links = data.get("links", [])

        # 画像URL: [https://...jpg] 記法や Gyazo URL
        image_urls = self._extract_image_urls(text_lines)

        # 外部URL: [https://...] 記法（画像以外）
        external_urls = self._extract_external_urls(text_lines)

        return ScrapboxPage(
            id=data.get("id", ""),
            title=data.get("title", ""),
            created=data.get("created", 0),
            updated=data.get("updated", 0),
            links=links,
            image_urls=image_urls,
            external_urls=external_urls,
            text=text,
            line_count=len(lines),
        )

    def _extract_image_urls(self, lines: list[str]) -> list[str]:
        import re
        urls = []
        # [URL] 記法の画像
        pattern = re.compile(r"\[([^\]]+\.(png|jpg|jpeg|gif|webp|svg))\]", re.IGNORECASE)
        gyazo = re.compile(r"\[(https://(?:gyazo\.com|i\.gyazo\.com)/[^\]]+)\]")
        for line in lines:
            for m in pattern.finditer(line):
                urls.append(m.group(1))
            for m in gyazo.finditer(line):
                urls.append(m.group(1))
        return list(dict.fromkeys(urls))  # 重複除去・順序保持

    def _extract_external_urls(self, lines: list[str]) -> list[str]:
        import re
        urls = []
        pattern = re.compile(r"\[(https?://[^\]\s]+)\]")
        image_ext = re.compile(r"\.(png|jpg|jpeg|gif|webp|svg)$", re.IGNORECASE)
        for line in lines:
            for m in pattern.finditer(line):
                url = m.group(1)
                if not image_ext.search(url) and "gyazo.com" not in url:
                    urls.append(url)
        return list(dict.fromkeys(urls))

    def fetch_all_pages(self, rate_limit_sec: float = 1.0) -> list[ScrapboxPage]:
        """全ページを取得して返す。rate_limit_sec 秒間隔でリクエスト。"""
        pages = []
        skip = 0
        limit = 100

        while True:
            result = self.list_pages(limit=limit, skip=skip)
            items = result.get("pages", [])
            if not items:
                break

            for item in items:
                try:
                    page = self.get_page(item["title"])
                    pages.append(page)
                    time.sleep(rate_limit_sec)
                except Exception as e:
                    print(f"  [skip] {item.get('title', '?')}: {e}")

            skip += len(items)
            if skip >= result.get("count", 0):
                break

        return pages
