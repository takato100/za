# 進められる作業リスト

takatoの意思決定を待たずに進められるもの。

---

## 今すぐ着手可能（Phase 0）

### P0-1: scrapbox-sync の実装（認証部分はスタブ） ✅ 完了
- ScrapboxClient, PageStorage, Syncer 実装済み
- **残り：** T-01（プロジェクト名・認証）解決でフル動作

### P0-2: link-graph の実装 ✅ 完了
- LinkGraph（networkx）, GraphStorage（SQLite）, find_privileged_pairs 実装済み

### P0-3: rag-index の実装 ✅ 完了
- Chunker, RAGIndex（OpenAI stub付き）, search 実装済み
- **残り：** T-02（Embedding API選択）解決で本番動作

### P0-4: 「間のリンク」検出ロジック
- link-graph + rag-indexを組み合わせた gap_score 計算
- threshold の実測チューニング
- **ブロッカー：** T-01解決後に実データで調整

### P0-5: image-segmentation のプロンプト設計と検証 ✅ 完了
- Scrapbox記法パーサー, Segmenter（Anthropic API stub付き）実装済み
- **残り：** 実際のScrapboxページ10〜20ページで精度検証（T-01後）

### P0-6: fragment-selector の実装（CLI）
- SelectionResult を返すコア関数
- 近傍70% / 跳躍30% の重み付きランダム選択
- **ブロッカー：** P0-4完了後

### P0-7: generation-engine の検証（CLI）
- Claude API呼び出し + 編集プロンプトの初期版
- 出力HTMLの確認（目視）
- **ブロッカー：** P0-6完了後。T-04（人格設計）は仮プロンプトで先行可能

---

## Phase 1 準備（T-03決定後に着手）

### P1-1: iOSプロジェクト作成（SwiftUI + WidgetKit）
- Xcodeプロジェクト雛形
- AppGroup設定
- WKWebViewの基本実装

### P1-2: web-rendererのHTMLテンプレート設計
- エディトリアルCSSの基本スタイル
- セクションタイプ別レイアウト
- 出典インジケータ

---

## 実装順序（推奨）

```
P0-2（link-graph）
P0-3（rag-index）   ← 並列で進められる
P0-5（image-segmentation）

↓

P0-1（scrapbox-sync） ← T-01解決後

↓

P0-4（間のリンク検出）

↓

P0-6（fragment-selector CLI）

↓

P0-7（generation-engine CLI）

↓ Phase 0 完了 ↓

P1-1, P1-2 ...
```
