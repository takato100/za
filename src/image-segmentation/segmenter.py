import json
import logging
from dataclasses import asdict

from .models import ImageUnit, ImageUnitType
from .parser import Block

logger = logging.getLogger(__name__)

SEGMENTATION_PROMPT = """
あなたはScrapboxのページ断片を「イマージュ」に分節する専門家です。

イマージュとは「知覚的に自立した断片」です。
- 一語でも意味的に完結していればイマージュ
- 複数の行がセットで初めて意味を持つ場合は一つのイマージュ
- メディア形式ではなく「知覚的なまとまり」で判断する

以下のブロックリストを入力として、イマージュのグルーピングをJSON形式で返してください。
各イマージュは以下のフィールドを持ちます：
- blocks: グルーピングしたブロックのインデックスリスト
- type: "text" / "image" / "text+image" / "url"
- summary: イマージュの内容を一行で（判断根拠用、出力には使わない）

入力ブロック:
{blocks_json}

JSON形式で返してください:
{{"images": [{{"blocks": [0, 1], "type": "text", "summary": "..."}}]}}
"""

# バッチ処理のしきい値
_BATCH_SIZE = 20


def _block_to_dict(index: int, block: Block) -> dict:
    """Block をプロンプト用の辞書に変換する。"""
    return {
        "index": index,
        "lines": block.lines,
        "has_image": block.has_image,
        "image_urls": block.image_urls,
        "external_urls": block.external_urls,
        "is_heading": block.is_heading,
        "indent_level": block.indent_level,
    }


def _type_from_str(type_str: str) -> ImageUnitType:
    mapping = {
        "text": ImageUnitType.TEXT,
        "image": ImageUnitType.IMAGE,
        "text+image": ImageUnitType.TEXT_IMAGE,
        "url": ImageUnitType.URL,
    }
    return mapping.get(type_str, ImageUnitType.TEXT)


def _infer_type_from_blocks(blocks: list[Block]) -> ImageUnitType:
    """ブロックの内容からイマージュ種別を推定する（スタブ用）。"""
    has_image = any(b.has_image for b in blocks)
    has_url = any(b.external_urls for b in blocks)
    has_text = any(
        any(line.strip() and not line.strip().startswith("[http") for line in b.lines)
        for b in blocks
    )

    if has_image and has_text:
        return ImageUnitType.TEXT_IMAGE
    if has_image:
        return ImageUnitType.IMAGE
    if has_url and not has_text:
        return ImageUnitType.URL
    return ImageUnitType.TEXT


def _blocks_to_content(blocks: list[Block]) -> str:
    """複数ブロックのテキストを結合する。"""
    return "\n\n".join("\n".join(b.lines) for b in blocks)


def _blocks_to_media_url(blocks: list[Block]) -> str | None:
    """ブロック群から最初のメディアURL（画像 or 外部URL）を取得する。"""
    for b in blocks:
        if b.image_urls:
            return b.image_urls[0]
        if b.external_urls:
            return b.external_urls[0]
    return None


class Segmenter:
    def __init__(self, api_key: str | None = None) -> None:
        """
        api_key: AnthropicのAPIキー。
        Noneの場合、またはanthropicライブラリが利用できない場合はスタブ動作。
        """
        self._client = None

        if api_key is not None:
            try:
                import anthropic  # type: ignore

                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized.")
            except ImportError:
                logger.warning(
                    "anthropic ライブラリが見つかりません。スタブ動作に切り替えます。"
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def segment(self, page_id: str, blocks: list[Block]) -> list[ImageUnit]:
        """BlockリストをイマージュにグルーピングしてImageUnitリストを返す。

        ブロック数が _BATCH_SIZE 以上の場合はバッチ処理を行う。
        LLMクライアントが利用できない場合はスタブにフォールバックする。
        """
        if self._client is None:
            return self._stub_segment(page_id, blocks)

        try:
            return self._llm_segment(page_id, blocks)
        except Exception as exc:
            logger.error("LLM分節中にエラーが発生しました: %s。スタブにフォールバックします。", exc)
            return self._stub_segment(page_id, blocks)

    # ------------------------------------------------------------------
    # LLM-based segmentation
    # ------------------------------------------------------------------

    def _llm_segment(self, page_id: str, blocks: list[Block]) -> list[ImageUnit]:
        """LLMを使ってブロックをイマージュに分節する。"""
        units: list[ImageUnit] = []
        position = 0

        # ブロック数が多い場合はバッチに分割して処理する
        for batch_start in range(0, len(blocks), _BATCH_SIZE):
            batch = blocks[batch_start : batch_start + _BATCH_SIZE]
            batch_units = self._llm_segment_batch(
                page_id=page_id,
                blocks=batch,
                global_offset=batch_start,
                position_start=position,
            )
            units.extend(batch_units)
            position += len(batch_units)

        return units

    def _llm_segment_batch(
        self,
        page_id: str,
        blocks: list[Block],
        global_offset: int,
        position_start: int,
    ) -> list[ImageUnit]:
        """単一バッチをLLMで処理してImageUnitリストを返す。"""
        blocks_json = json.dumps(
            [_block_to_dict(i, b) for i, b in enumerate(blocks)],
            ensure_ascii=False,
            indent=2,
        )
        prompt = SEGMENTATION_PROMPT.format(blocks_json=blocks_json)

        message = self._client.messages.create(  # type: ignore[union-attr]
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        # JSONブロックを抽出（```json ... ``` で囲まれている場合も考慮）
        json_text = self._extract_json(response_text)
        data = json.loads(json_text)

        units: list[ImageUnit] = []
        for idx, image_data in enumerate(data.get("images", [])):
            local_indices: list[int] = image_data.get("blocks", [])
            grouped_blocks = [
                blocks[i] for i in local_indices if 0 <= i < len(blocks)
            ]
            if not grouped_blocks:
                continue

            unit_type = _type_from_str(image_data.get("type", "text"))
            content = _blocks_to_content(grouped_blocks)
            media_url = _blocks_to_media_url(grouped_blocks)
            position = position_start + idx

            units.append(
                ImageUnit(
                    id=f"{page_id}::{position}",
                    page_id=page_id,
                    unit_type=unit_type,
                    content=content,
                    media_url=media_url,
                    position=position,
                )
            )

        return units

    @staticmethod
    def _extract_json(text: str) -> str:
        """レスポンステキストからJSON部分を取り出す。"""
        # ```json ... ``` ブロックがあれば中身だけ使う
        import re

        code_block = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
        if code_block:
            return code_block.group(1).strip()

        # { で始まる最初のJSONオブジェクトを探す
        start = text.find("{")
        if start != -1:
            return text[start:]

        return text

    # ------------------------------------------------------------------
    # Stub segmentation
    # ------------------------------------------------------------------

    def _stub_segment(self, page_id: str, blocks: list[Block]) -> list[ImageUnit]:
        """LLMなしのフォールバック：各ブロックをそのままImageUnitに変換する。"""
        units: list[ImageUnit] = []
        for position, block in enumerate(blocks):
            unit_type = _infer_type_from_blocks([block])
            content = _blocks_to_content([block])
            media_url = _blocks_to_media_url([block])

            units.append(
                ImageUnit(
                    id=f"{page_id}::{position}",
                    page_id=page_id,
                    unit_type=unit_type,
                    content=content,
                    media_url=media_url,
                    position=position,
                )
            )

        return units
