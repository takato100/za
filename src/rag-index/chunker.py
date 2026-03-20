from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    id: str           # "{page_id}::{chunk_index}"
    page_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def _approx_tokens(text: str) -> int:
    """日本語混在を考慮したトークン数近似: len(text) // 3"""
    return len(text) // 3


def _split_into_sentences(text: str) -> list[str]:
    """テキストを文単位に分割する。"""
    # 句点・ピリオド・感嘆符・疑問符で分割（区切り文字を含む）
    parts = re.split(r'(?<=[。．.!?！？])', text)
    return [p for p in parts if p]


def chunk_text(page_id: str, text: str, max_tokens: int = 400) -> list[Chunk]:
    """
    段落（空行区切り）で分割し、max_tokensを超える場合は文で追加分割。
    トークン数の近似: len(text) // 3（日本語混在のため）
    """
    if not text:
        return []

    # 段落分割: 空行（1行以上の空行）で区切る
    paragraph_pattern = re.compile(r'\n\s*\n')
    raw_paragraphs: list[tuple[str, int]] = []  # (text, start_offset)

    last_end = 0
    for m in paragraph_pattern.finditer(text):
        para = text[last_end:m.start()]
        if para.strip():
            raw_paragraphs.append((para, last_end))
        last_end = m.end()

    # 末尾の段落
    remaining = text[last_end:]
    if remaining.strip():
        raw_paragraphs.append((remaining, last_end))

    # 段落ごとにmax_tokensチェックし、必要なら文分割
    segments: list[tuple[str, int]] = []  # (text, char_start)

    for para_text, para_start in raw_paragraphs:
        if _approx_tokens(para_text) <= max_tokens:
            segments.append((para_text, para_start))
        else:
            # 文で分割してmax_tokens以内にまとめる
            sentences = _split_into_sentences(para_text)
            current_buf: list[str] = []
            current_start: int = para_start
            current_len: int = 0

            for sentence in sentences:
                sent_tokens = _approx_tokens(sentence)
                if current_buf and current_len + sent_tokens > max_tokens:
                    # 現在のバッファをフラッシュ
                    joined = "".join(current_buf)
                    segments.append((joined, current_start))
                    # 次のバッファの開始位置を計算
                    current_start = current_start + len(joined)
                    current_buf = [sentence]
                    current_len = sent_tokens
                else:
                    if not current_buf:
                        # バッファの先頭: para内のオフセットを計算
                        offset_in_para = para_text.find(sentence)
                        if offset_in_para >= 0:
                            current_start = para_start + offset_in_para
                    current_buf.append(sentence)
                    current_len += sent_tokens

            if current_buf:
                segments.append(("".join(current_buf), current_start))

    # Chunkオブジェクトに変換
    chunks: list[Chunk] = []
    for chunk_index, (seg_text, char_start) in enumerate(segments):
        char_end = char_start + len(seg_text)
        chunk = Chunk(
            id=f"{page_id}::{chunk_index}",
            page_id=page_id,
            chunk_index=chunk_index,
            text=seg_text,
            char_start=char_start,
            char_end=char_end,
        )
        chunks.append(chunk)

    return chunks
