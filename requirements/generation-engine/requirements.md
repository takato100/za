# generation-engine 要件

## 責務
fragment-selectorが選んだ断片群を受け取り、LLMが「編集」を行ってwebページコンテンツを生成する。

## 編集の原則（最重要）
| 原則 | 詳細 |
|------|------|
| 要約しない | 断片をそのまま使う。圧縮しない |
| 関係を説明しない | 素材間の繋がりを言語化しない |
| 並べ、余白で繋ぐ | 素材の配置と順序で意味を作る |
| 変奏する | 同じ焦点から毎回異なるページを生成 |
| 本歌取り | ユーザーの記述を踏まえつつずらす |

## LLMへの指示（プロンプト設計の方針）
- agentはDJ。キュレーターでもナレーターでもない
- 生成物にagentの「声」を出さない
- 素材の並び順・取捨選択・余白の設計だけを行う
- 過去の生成履歴を参照し、同一の組み合わせを回避

## 入力
- SelectionResult（focal_image + neighbors + leaps）
- 過去の生成履歴（重複回避用）

## 出力
```
GeneratedPage {
    id: str              # UUID
    created_at: timestamp
    focal_image_id: str
    sections: list[Section]   # 配置済みの断片リスト（順序付き）
    layout_hints: dict        # web-rendererへのレイアウト指示
}

Section {
    image_unit: ImageUnit
    role: enum   # focal / context / leap
    spacing: enum  # tight / loose / break（余白の量）
}
```

## 技術選定
- Claude API（claude-opus-4-6 or claude-sonnet-4-6）
- Phase 0はsonnetで検証（コスト重視）→ Phase 1でopusに切り替え検討

## 一回性の保証
- 過去の GeneratedPage の `focal_image_id` + `section ids` の組み合わせをハッシュ化して記録
- 同一ハッシュが出たら再生成

## 未決定事項
- [ ] **[takato-task P2]** agentの人格設計の詳細（編集スタイルのプロンプト）
- [ ] **[takato-task P2]** 生成頻度（日に2-3回の「非等間隔」の具体的な実装方法）
- [ ] 過去履歴の保持期間（地層として何世代分を重複回避対象にするか）
