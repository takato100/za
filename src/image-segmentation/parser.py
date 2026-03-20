import re
from dataclasses import dataclass, field


# 画像URLとみなす拡張子・ホストのパターン
_IMAGE_URL_RE = re.compile(
    r'\[('
    r'https?://[^\s\[\]]+\.(?:png|jpg|jpeg|gif|webp|svg)'
    r'|https?://gyazo\.com/[^\s\[\]]+'
    r'|https?://i\.imgur\.com/[^\s\[\]]+'
    r')\]',
    re.IGNORECASE,
)

# 外部URLパターン（画像以外の [https://...] 記法）
_EXTERNAL_URL_RE = re.compile(r'\[(https?://[^\s\[\]]+)\]')

# 見出し記法 [* text] [** text] など
_HEADING_RE = re.compile(r'^\[(\*+)\s+.+\]$')

# 行頭インデント（半角スペース）
_INDENT_RE = re.compile(r'^( *)')


@dataclass
class Block:
    lines: list[str]
    has_image: bool
    image_urls: list[str]
    external_urls: list[str]
    is_heading: bool     # [* text] 記法
    indent_level: int    # インデントの深さ（先頭行の値）


def extract_image_urls(line: str) -> list[str]:
    """[...] 記法から画像URLを抽出する。"""
    return _IMAGE_URL_RE.findall(line)


def extract_external_urls(line: str) -> list[str]:
    """[...] 記法から外部URLを抽出する（画像URLは除く）。"""
    candidates = _EXTERNAL_URL_RE.findall(line)
    image_urls = set(extract_image_urls(line))
    return [url for url in candidates if url not in image_urls]


def _indent_level(line: str) -> int:
    """行頭スペース数を返す。"""
    m = _INDENT_RE.match(line)
    return len(m.group(1)) if m else 0


def _is_heading(line: str) -> bool:
    """行が見出し記法かどうかを判定する。"""
    return bool(_HEADING_RE.match(line.strip()))


def _build_block(lines: list[str]) -> Block:
    """行リストから Block を構築する。"""
    image_urls: list[str] = []
    external_urls: list[str] = []

    for line in lines:
        image_urls.extend(extract_image_urls(line))
        external_urls.extend(extract_external_urls(line))

    first_line = lines[0] if lines else ""
    return Block(
        lines=lines,
        has_image=len(image_urls) > 0,
        image_urls=image_urls,
        external_urls=external_urls,
        is_heading=_is_heading(first_line),
        indent_level=_indent_level(first_line),
    )


def parse_scrapbox_page(text: str) -> list[Block]:
    """Scrapboxのページ本文を Block のリストに分割する。

    Scrapbox記法:
    - [画像URL.png] or [https://gyazo.com/xxx] → 画像
    - [https://example.com] → 外部URL
    - [* テキスト] [** テキスト] → 見出し
    - 空行 → ブロック区切り
    - 行頭スペース → インデント
    """
    raw_lines = text.splitlines()
    blocks: list[Block] = []
    current_lines: list[str] = []

    for line in raw_lines:
        if line.strip() == "":
            # 空行はブロック区切り
            if current_lines:
                blocks.append(_build_block(current_lines))
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        blocks.append(_build_block(current_lines))

    return blocks
