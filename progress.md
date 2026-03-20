# 進められる作業リスト

takatoの意思決定を待たずに進められるもの。

---

## 今すぐ着手可能（Phase 0）

### P0-1: scrapbox-sync の実装（認証部分はスタブ）
- Scrapbox APIクライアントの実装（認証は `.env` から読む空実装で）
- ページ一覧取得・本文取得の関数
- SQLiteへの保存
- **ブロッカー：** T-01（プロジェクト名・認証）だけ。認証なしのパブリックプロジェクトで先行検証可能

### P0-2: link-graph の実装
- networkx グラフの構築ロジック
- SQLiteへのシリアライズ/デシリアライズ
- BFS（N ホップ探索）の実装
- co-linkエッジの検出
- **ブロッカー：** なし。サンプルデータで実装・テスト可能

### P0-3: rag-index の実装（API選択は仮でOpenAI）
- テキストチャンク化ロジック
- embedding生成・SQLiteへの保存
- コサイン類似度検索
- **ブロッカー：** T-02。ただしOpenAI仮決定で進めて後から差し替え可能

### P0-4: 「間のリンク」検出ロジック
- link-graph + rag-indexを組み合わせた gap_score 計算
- threshold の実測チューニング
- **ブロッカー：** P0-2, P0-3が完了してから

### P0-5: image-segmentation のプロンプト設計と検証
- Scrapbox記法パーサー（行・ブロック分割）
- LLMへのイマージュ分節プロンプト（複数案を設計して比較）
- 実際のScrapboxページ10〜20ページで精度検証
- **ブロッカー：** なし（サンプルテキストで先行開発可能）

### P0-6: fragment-selector の実装（CLI）
- SelectionResult を返すコア関数
- 近傍70% / 跳躍30% の重み付きランダム選択
- **ブロッカー：** P0-2, P0-4が完了してから

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
