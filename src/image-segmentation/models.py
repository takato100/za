from dataclasses import dataclass
from enum import Enum


class ImageUnitType(Enum):
    TEXT = "text"
    IMAGE = "image"
    TEXT_IMAGE = "text+image"
    URL = "url"


@dataclass
class ImageUnit:
    id: str              # "{page_id}::{index}"
    page_id: str
    unit_type: ImageUnitType
    content: str         # テキスト内容
    media_url: str | None  # 画像/URLがある場合
    position: int        # ページ内の順序
