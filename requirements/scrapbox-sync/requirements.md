# scrapbox-sync 要件

## 責務
Scrapbox APIからユーザーのプロジェクトデータを取得し、ローカルに永続化する。
他コンポーネント（link-graph, rag-index, image-segmentation）のデータソースとなる。

## 入力
- Scrapboxプロジェクト名
- 認証情報（Cookieベース: `connect.sid`）

## 出力（ローカルストレージ）
- ページ一覧（タイトル、作成日、更新日、リンクリスト）
- ページ本文（プレーンテキスト）
- ページ内画像URL
- ページ内外部URL

## APIエンドポイント（Scrapbox非公式API）
| エンドポイント | 用途 |
|-------------|------|
| `GET /api/pages/:project` | ページ一覧（limit/skipでページネーション） |
| `GET /api/pages/:project/:title` | ページ詳細（本文、リンク、画像含む） |

## 同期方式
- **初回：** 全ページ取得
- **差分：** `updated` タイムスタンプ比較による増分更新
- バックグラウンド実行。UIをブロックしない

## ストレージ設計（Phase 0）
- SQLite（`pages` テーブル）
- JSON形式でページ本文を保存
- インデックス：`title`, `updated`

## 制約・リスク
- Scrapbox APIは非公式。仕様変更リスクあり
- rate limitの明示的な規定なし → 1リクエスト/秒以下で抑制
- プライベートプロジェクトはCookie認証必須

## 未決定事項
- [ ] **[takato-task]** Scrapboxプロジェクト名と認証情報の提供方法（ローカル設定ファイル or 環境変数）
- [ ] **[takato-task]** 同期頻度（Phase 0は手動実行で可）
