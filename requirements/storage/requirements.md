# storage 要件

## 責務
生成されたwebページを時系列で保存する（地層）。
目的は再体験ではなく、螺旋の軌跡の観察。

## 設計思想
- 地層：削除しない。上書きしない。積み重なる
- 同じ焦点から異なる時点で生成されたページを比較可能に
- 保存したことをユーザーに通知しない（罪悪感・達成感を生まない）

## データモデル
```
Stratum {
    id: str                  # UUID
    created_at: timestamp
    focal_image_id: str
    generated_page_id: str
    html_content: str        # 生成されたHTML
    selection_snapshot: JSON # その時点でのSelectResultのスナップショット
}
```

## クエリ
- 同一 `focal_image_id` の地層を時系列で取得
- 全地層の一覧（閲覧用）

## 技術選定
- SQLite（Phase 0〜1）
- HTMLはテキストのままDBに保存（Phase 0）
  → ファイルシステム保存（Phase 1以降）に移行検討

## 閲覧UI（Phase 2以降）
- 地層の閲覧はアプリ内の別ビュー
- 同一焦点の複数バージョンを並べて比較
- 操作：スクロールのみ。削除ボタンなし

## 未決定事項
- [ ] 保持する地層の上限（ストレージ容量）→ Phase 1で実測して決定
