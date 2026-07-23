#!/usr/bin/env python3
"""
便签 / 待办（provider: notes）

创建笔记 create_note —— 参数 title + content + folder_id

在 Cursor 已连接 notes MCP 时，可由 Agent 直接调用同名工具；
本脚本提供可复用的 create_note()，并在 MCP 不可用时回退到本地记事本文件（.txt），
以便演示与无人值守运行。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class NoteResult:
    ok: bool
    provider: str
    note_id: str
    path_or_uri: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("._")
    return (cleaned or "note")[:80]


def create_note(
    title: str,
    content: str,
    folder_id: str = "",
    *,
    notes_dir: str | Path | None = None,
) -> NoteResult:
    """
    创建一条笔记。

    参数（与 notes provider 对齐）：
      - title: 笔记标题
      - content: 笔记正文
      - folder_id: 文件夹/笔记本 ID（可空；本地回退时作为子目录名）

    解析顺序：
      1) 若设置 JOB_NOTES_WEBHOOK_URL，则 POST JSON 到该 Webhook（可接自建 notes 桥）
      2) 否则写入本地记事本目录（默认 ~/.job-outreach/notes/）
    """
    title = (title or "").strip() or "未命名笔记"
    content = content or ""
    folder_id = (folder_id or "").strip()

    webhook = os.environ.get("JOB_NOTES_WEBHOOK_URL", "").strip()
    if webhook:
        payload = {"title": title, "content": content, "folder_id": folder_id}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook,
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "job-application-email-skill/notes",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            note_id = ""
            try:
                parsed = json.loads(body)
                note_id = str(parsed.get("id") or parsed.get("note_id") or "")
            except json.JSONDecodeError:
                note_id = ""
            return NoteResult(
                True,
                "notes_webhook",
                note_id or "webhook",
                webhook,
                body[:300] or "created via webhook",
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Webhook 失败则回退本地，保证演示可继续
            fallback_msg = f"webhook failed: {exc}; fallback to local notepad"
        else:
            fallback_msg = ""
    else:
        fallback_msg = "notes MCP/webhook unavailable; using local notepad"

    base = Path(notes_dir or os.path.expanduser("~/.job-outreach/notes")).expanduser()
    if folder_id:
        base = base / _safe_filename(folder_id)
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = base / f"{stamp}_{_safe_filename(title)}.txt"
    text = f"{title}\n{'=' * len(title)}\n\n{content}\n"
    if folder_id:
        text = f"[folder_id={folder_id}]\n" + text
    path.write_text(text, encoding="utf-8")
    return NoteResult(
        True,
        "local_notepad",
        path.stem,
        str(path),
        fallback_msg,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="create_note (provider: notes)")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", default="")
    parser.add_argument("--content-file", help="从文件读取 content")
    parser.add_argument("--folder-id", default="")
    parser.add_argument("--notes-dir", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    content = args.content
    if args.content_file:
        content = Path(args.content_file).expanduser().read_text(encoding="utf-8")

    result = create_note(
        args.title,
        content,
        args.folder_id,
        notes_dir=args.notes_dir or None,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(
            f"{'OK' if result.ok else 'FAIL'} provider={result.provider} "
            f"id={result.note_id} path={result.path_or_uri} msg={result.message}"
        )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
