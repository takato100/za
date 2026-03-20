"""
PDMエージェント — 「輝きの再点火」プロジェクト

プロダクト開発マネージャーとして機能するエージェント。
最終責任者 takato への報告を怠らない。

Anthropic API + ツール使用による実装（Agent SDK非依存）
"""

import anthropic
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path("/home/user/za")

SYSTEM_PROMPT = """
あなたはプロダクト開発マネージャー（PDM）エージェントです。
プロジェクト「輝きの再点火」の開発を管理・推進します。

## あなたの役割
- 要件定義・仕様の整理と具体化
- 技術的な判断と設計提案
- 開発上の課題の発見と解決策の提示
- 進捗の可視化

## 最重要ルール：報告義務
**すべての判断・提案の前後に必ず takato へ報告する。**

報告のフォーマット：
```
【報告】
状況：[現在何をしているか]
判断・提案：[何をしようとしているか、なぜか]
確認事項：[takato に判断を仰ぐ点があれば明記。なければ「なし」]
```

一人で決めない。takato が最終責任者。
重要な判断は必ず「確認事項」として明示し、承認を得てから進む。

## プロジェクト文脈
- Scrapboxユーザーの思考の「輝き」を再点火する装置
- Layer構成：L1（ウィジェット）→ L2（生成Webページ）→ L3（外部リンク）
- コア技術：Scrapboxリンクグラフ（グラフDB）+ RAGインデックス（チャンクのみ）+ Claude API
- 設計原則：最適化しすぎない、押し売りしない、説明しない
- リンクグラフとRAGインデックスは独立した2データストア

## ファイル構成
- requirements/requirements.md : 要件定義書（必ず参照する）
- discussions/summary.md : 七者討論サマリー
- discussions/*.md : 各参加者のレポート
"""

TOOLS = [
    {
        "name": "read_file",
        "description": "プロジェクト内のファイルを読む",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "BASE_DIR（/home/user/za）からの相対パス。例: requirements/requirements.md",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "プロジェクト内のファイル一覧を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "BASE_DIRからの相対パス。空文字でルート",
                    "default": "",
                }
            },
            "required": [],
        },
    },
    {
        "name": "write_file",
        "description": "プロジェクト内のファイルに書き込む（新規作成・上書き）",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "書き込み先の相対パス"},
                "content": {"type": "string", "description": "書き込む内容"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, input_data: dict) -> str:
    if name == "read_file":
        file_path = BASE_DIR / input_data["path"]
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"ERROR: ファイルが見つかりません: {input_data['path']}"
        except Exception as e:
            return f"ERROR: {e}"

    elif name == "list_files":
        directory = input_data.get("directory", "")
        target = BASE_DIR / directory if directory else BASE_DIR
        try:
            entries = []
            for p in sorted(target.rglob("*")):
                if p.is_file() and ".git" not in p.parts:
                    entries.append(str(p.relative_to(BASE_DIR)))
            return "\n".join(entries) if entries else "(空)"
        except Exception as e:
            return f"ERROR: {e}"

    elif name == "write_file":
        file_path = BASE_DIR / input_data["path"]
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(input_data["content"], encoding="utf-8")
            return f"OK: {input_data['path']} に書き込みました"
        except Exception as e:
            return f"ERROR: {e}"

    return f"ERROR: 未知のツール {name}"


def run_pdm(task: str) -> None:
    client = anthropic.Anthropic()

    print(f"\n{'='*60}")
    print("PDMエージェント起動")
    print(f"タスク: {task}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # レスポンス内容を表示
        for block in response.content:
            if block.type == "thinking":
                print(f"\n[thinking] {block.thinking[:200]}..." if len(block.thinking) > 200 else f"\n[thinking] {block.thinking}")
            elif block.type == "text":
                print(f"\n{block.text}")
            elif block.type == "tool_use":
                print(f"\n[tool: {block.name}] {json.dumps(block.input, ensure_ascii=False)[:100]}")

        if response.stop_reason == "end_turn":
            print(f"\n{'='*60}")
            print("PDMエージェント 完了")
            print(f"{'='*60}")
            break

        if response.stop_reason != "tool_use":
            print(f"\n[停止: {response.stop_reason}]")
            break

        # ツール実行
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                print(f"  → {result[:80]}..." if len(result) > 80 else f"  → {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    # APIキーが環境変数にない場合は引数で受け取れる
    # 例: python3 pdm_agent.py --api-key sk-ant-xxx "タスク"
    args = sys.argv[1:]
    if args and args[0] == "--api-key":
        os.environ["ANTHROPIC_API_KEY"] = args[1]
        args = args[2:]

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY が設定されていません。")
        print("使い方: ANTHROPIC_API_KEY=sk-ant-xxx python3 pdm_agent.py")
        print("または: python3 pdm_agent.py --api-key sk-ant-xxx")
        sys.exit(1)

    if args:
        task = " ".join(args)
    else:
        task = (
            "要件定義書（requirements/requirements.md）と七者討論サマリー（discussions/summary.md）を読んで、"
            "現在の未決定事項を整理し、次に詰めるべき開発要件をまとめてください。"
            "特にPhase 0の検証で最初に実装すべきことを具体化し、"
            "takatoへの報告として出力してください。"
        )

    run_pdm(task)
