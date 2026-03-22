# Scrapbox MCP セットアップ

## 1. 依存インストール

```bash
cd /path/to/za/mcp
pip install -r requirements.txt
```

## 2. 環境変数を ~/.zshrc に追加 (TODO)

```zsh
export SCRAPBOX_PROJECT="your-project-name"
export SCRAPBOX_CONNECT_SID="your-connect-sid-value"
```

`connect.sid` の取得: Chrome で scrapbox.io を開き、
DevTools > Application > Cookies > connect.sid の Value をコピー。

## 3. Claude Code の MCP 設定

`~/.claude/settings.json` に追記:

```json
{
  "mcpServers": {
    "scrapbox": {
      "command": "python",
      "args": ["/path/to/za/mcp/server.py"],
      "env": {
        "SCRAPBOX_PROJECT": "${SCRAPBOX_PROJECT}",
        "SCRAPBOX_CONNECT_SID": "${SCRAPBOX_CONNECT_SID}"
      }
    }
  }
}
```

## 4. インデックス初回構築

Claude Code 上で:
```
scrapbox_rebuild_index を呼んで
```

初回はモデルダウンロード (~120MB) + embedding 計算で数分かかる。
以降は `~/.scrapbox_mcp/` にキャッシュされる。

## ツール一覧

| ツール | 用途 |
|--------|------|
| `scrapbox_rebuild_index` | Scrapbox から全ページ取得 + index 再構築 |
| `scrapbox_search` | 意味的類似検索 |
| `scrapbox_hop` | リンクグラフ近傍探索（付きすぎず離れすぎず） |
| `scrapbox_jump` | 弱いリンク発見（間のリンク、本歌取りの距離感） |
| `scrapbox_surface` | ランダム/seed付きページ浮かび上がり |
| `scrapbox_page` | 特定ページの内容読み取り |
