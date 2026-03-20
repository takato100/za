"""
PDMエージェント — 「輝きの再点火」プロジェクト

プロダクト開発マネージャーとして機能するエージェント。
最終責任者 takato への報告を怠らない。
"""

import anyio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, SystemMessage

SYSTEM_PROMPT = """
あなたはプロダクト開発マネージャー（PDM）エージェントです。
プロジェクト「輝きの再点火」の開発を管理・推進します。

## あなたの役割
- 要件定義・仕様の整理と具体化
- 技術的な判断と設計提案
- 開発上の課題の発見と解決策の提示
- 進捗の可視化

## 最重要ルール：報告義務
**すべてのタスクの開始前・終了後・判断を下す前に必ず takato に報告する。**

報告のフォーマット：
```
【報告】
状況：[現在何をしているか]
判断・提案：[何をしようとしているか、なぜか]
確認事項：[takato に判断を仰ぐ点があれば明記]
```

一人で決めない。takato が最終責任者。
重要な判断は必ず「確認事項」として明示し、承認を得てから進む。

## プロジェクト文脈
- Scrapboxユーザーの思考の「輝き」を再点火する装置
- Layer構成：L1（ウィジェット）→ L2（生成Webページ）→ L3（外部リンク）
- コア技術：Scrapboxリンクグラフ（グラフDB）+ RAGインデックス（チャンクのみ）+ Claude API
- 設計原則：最適化しすぎない、押し売りしない、説明しない

## 参照ファイル
- requirements/requirements.md : 要件定義書
- discussions/ : 七者討論のレポート群
"""


async def run_pdm(task: str) -> None:
    """PDMエージェントにタスクを実行させる"""

    print(f"\n{'='*60}")
    print(f"PDMエージェント起動")
    print(f"タスク: {task}")
    print(f"{'='*60}\n")

    async for message in query(
        prompt=task,
        options=ClaudeAgentOptions(
            cwd="/home/user/za",
            allowed_tools=["Read", "Glob", "Grep", "Write", "Edit"],
            system_prompt=SYSTEM_PROMPT,
            model="claude-opus-4-6",
            max_turns=20,
        ),
    ):
        if isinstance(message, ResultMessage):
            print("\n" + "="*60)
            print("【PDMエージェント 最終報告】")
            print("="*60)
            print(message.result)
            print(f"\n[停止理由: {message.stop_reason}]")
        elif isinstance(message, SystemMessage):
            if message.subtype == "init":
                session_id = message.data.get("session_id", "unknown")
                print(f"[セッションID: {session_id}]")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = (
            "要件定義書（requirements/requirements.md）を読んで、"
            "現在の未決定事項と次に詰めるべき開発要件を整理して報告してください。"
            "特にLayer2のScrapbox連携部分（リンクグラフとRAGインデックスの設計）について、"
            "Phase 0の検証で最初に実装すべきことを具体化してください。"
        )

    anyio.run(run_pdm, task)
