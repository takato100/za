"""Scrapbox 同期ロジック。"""
import time
from .client import ScrapboxClient
from .storage import PageStorage
from .models import SyncState


class Syncer:
    def __init__(self, project: str, db_path: str, cookie: str | None = None):
        self.client = ScrapboxClient(project, cookie)
        self.storage = PageStorage(db_path)
        self.project = project

    def full_sync(self, rate_limit_sec: float = 1.0) -> SyncState:
        """全ページを取得して保存する。"""
        print(f"[sync] full sync start: {self.project}")
        errors = []
        count = 0
        skip = 0
        limit = 100

        while True:
            result = self.client.list_pages(limit=limit, skip=skip)
            items = result.get("pages", [])
            if not items:
                break

            for item in items:
                title = item.get("title", "")
                try:
                    page = self.client.get_page(title)
                    self.storage.upsert_page(page)
                    count += 1
                    print(f"  [{count}] {title}")
                    time.sleep(rate_limit_sec)
                except Exception as e:
                    errors.append(f"{title}: {e}")
                    print(f"  [error] {title}: {e}")

            skip += len(items)
            total = result.get("count", 0)
            print(f"  progress: {skip}/{total}")
            if skip >= total:
                break

        state = SyncState(
            project=self.project,
            last_synced=int(time.time()),
            page_count=count,
            errors=errors,
        )
        self.storage.save_sync_state(state)
        print(f"[sync] done: {count} pages, {len(errors)} errors")
        return state

    def incremental_sync(self, rate_limit_sec: float = 1.0) -> SyncState:
        """前回同期以降に更新されたページのみ取得する。"""
        state = self.storage.get_sync_state(self.project)
        since_ts = state.last_synced if state else 0
        print(f"[sync] incremental sync since {since_ts}: {self.project}")

        errors = []
        count = 0
        skip = 0
        limit = 100

        while True:
            result = self.client.list_pages(limit=limit, skip=skip)
            items = result.get("pages", [])
            if not items:
                break

            updated_items = [p for p in items if p.get("updated", 0) > since_ts]
            if not updated_items:
                break  # 更新なし

            for item in updated_items:
                title = item.get("title", "")
                try:
                    page = self.client.get_page(title)
                    self.storage.upsert_page(page)
                    count += 1
                    print(f"  [update] {title}")
                    time.sleep(rate_limit_sec)
                except Exception as e:
                    errors.append(f"{title}: {e}")

            skip += len(items)
            if skip >= result.get("count", 0):
                break

        new_state = SyncState(
            project=self.project,
            last_synced=int(time.time()),
            page_count=(state.page_count if state else 0) + count,
            errors=errors,
        )
        self.storage.save_sync_state(new_state)
        print(f"[sync] incremental done: {count} updated")
        return new_state
