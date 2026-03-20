# link-graph 要件

## 責務
Scrapboxのページ間リンク構造をグラフとして構築・永続化し、グラフ探索クエリを提供する。
RAGインデックスとは**独立したデータストア**として設計する（リンク情報をembeddingに混入しない）。

## 入力
- scrapbox-sync が出力したページデータ（タイトル、リンクリスト、メタデータ）

## 出力（クエリAPI）
- 指定ページから N ホップ以内のノード一覧
- グラフ距離の計算
- 「間のリンク」候補（グラフ距離近い × embedding距離遠い）の検出 ← rag-indexと協調

## データモデル

### ノード（ページ）
| フィールド | 型 | 内容 |
|-----------|-----|------|
| id | str | ページタイトル（Scrapboxの識別子） |
| created | timestamp | 作成日 |
| updated | timestamp | 更新日 |
| link_count | int | 被リンク数 |
| text_length | int | 本文文字数 |

### エッジ（リンク）
| フィールド | 型 | 内容 |
|-----------|-----|------|
| source | str | リンク元ページID |
| target | str | リンク先ページID |
| type | enum | `direct` / `co-link`（共通リンク経由） |

## 技術選定（確定）
- **networkx**：グラフ探索（BFS/DFS, shortest_path, etc.）
- **SQLite**：永続化（グラフをJSONシリアライズして保存）
- Phase 1以降でグラフDB（Neo4j等）への移行を検討するが、Phase 0はこれで十分

## 「間のリンク」検出アルゴリズム（暫定）
```python
# グラフ距離 ≤ 2 かつ cosine similarity < threshold のノード対
# gap_score = threshold - cosine_similarity（乖離が大きいほど高スコア）
privileged_pairs = [
    (a, b, threshold - cosine_sim(emb[a], emb[b]))
    for a, b in pairs_within_hops(graph, max_hops=2)
    if cosine_sim(emb[a], emb[b]) < threshold
]
```
→ `threshold` はtakatoのScrapboxで実測して調整（初期値 0.6）

## 未決定事項
- [ ] co-linkエッジの定義精度（共通リンク数の閾値）
- [ ] 「間のリンク」の `threshold` 値 → Phase 0で実測して決定
