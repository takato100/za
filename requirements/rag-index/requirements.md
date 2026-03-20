# rag-index 要件

## 責務
Scrapboxページ本文をチャンク化しembeddingを生成・保存する。
**ページ本文のテキストチャンクのみを格納する。リンク情報は含めない。**

## 設計原則（重要）
リンクグラフとRAGインデックスは独立した2データストア。
- リンク先のテキストをチャンクに混入しない
- 理由：「意味的に遠いがリンクで繋がっている」という乖離を検出するため、embeddingはページ本文の純粋な意味を反映する必要がある
- embeddingは「間のリンク」検出の補助計算にのみ使用（メインの断片選択はグラフ探索）

## 入力
- scrapbox-sync が出力したページ本文テキスト

## 出力
- チャンク単位のembeddingベクトル
- コサイン類似度検索API
- ページ単位の代表ベクトル（チャンクの平均 or 先頭チャンク）

## チャンク設計
- 単位：段落（空行区切り）を基本とし、長すぎる場合は文で分割
- サイズ：200〜500トークン（オーバーラップなし）
- メタデータ：ページID、チャンク番号、文字位置

## 技術選定（確定）
- **Embedding API：** [要takato確認] OpenAI `text-embedding-3-small` or Claude
- **ベクトルストレージ：** SQLite + numpy（Phase 0） → Chroma or pgvector（Phase 1以降）
- **類似度計算：** cosineをnumpyで計算（Phase 0のデータ量なら十分）

## コスト概算（OpenAI text-embedding-3-small の場合）
- $0.02 / 1M tokens
- Scrapbox 1000ページ × 平均500トークン = 500K tokens → 約$0.01
- 初回インデックス構築はほぼ無視できるコスト

## 未決定事項
- [ ] **[takato-task P1]** Embedding APIの選択（OpenAI or Claude）
