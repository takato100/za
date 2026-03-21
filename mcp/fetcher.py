import httpx
from config import SCRAPBOX_PROJECT, SCRAPBOX_CONNECT_SID

BASE = "https://scrapbox.io/api"


def _headers() -> dict:
    return {"Cookie": f"connect.sid={SCRAPBOX_CONNECT_SID}"}


async def fetch_all_pages() -> list[dict]:
    """
    Fetch all pages from the Scrapbox project (paginated).
    Each page includes: title, descriptions (first few lines), links, updated.
    """
    pages = []
    skip = 0
    limit = 100

    async with httpx.AsyncClient(headers=_headers(), timeout=30) as client:
        while True:
            r = await client.get(
                f"{BASE}/pages/{SCRAPBOX_PROJECT}",
                params={"limit": limit, "skip": skip},
            )
            r.raise_for_status()
            data = r.json()
            batch = data.get("pages", [])
            if not batch:
                break
            pages.extend(batch)
            skip += len(batch)
            if skip >= data.get("count", 0):
                break

    return pages
