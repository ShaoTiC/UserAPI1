#!/usr/bin/env python3
"""
DroiClaw MCP · 便签 / 待办（provider: notes）

按能力手册命名规则：`{provider}_{tool_name}` → **notes_create_note**

创建笔记 notes_create_note
  参数：
    - title: str
    - content: str
    - folder_id: str

本模块对外主入口即 notes_create_note()；create_note() 为同名别名以兼容旧调用。

执行策略：
  1) 若设置 DROICLAW_MCP_URL / JOB_NOTES_WEBHOOK_URL：HTTP 调用真实 MCP/桥接
     （请求体含 tool=notes_create_note 与上述三参数）
  2) 否则写入本地记事本 .txt（演示回退；云端无手机 MCP 时使用）
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

# 手册规定的完整 Tool 名
TOOL_NAME = "notes_create_note"
PROVIDER = "notes"


@dataclass
class NoteResult:
    ok: bool
    tool: str
    provider: str
    note_id: str
    path_or_uri: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("._")
    return (cleaned or "note")[:80]


def _post_mcp(url: str, title: str, content: str, folder_id: str) -> NoteResult:
    """调用 DroiClaw / 桥接服务上的 notes_create_note。"""
    payload = {
        "tool": TOOL_NAME,
        "provider": PROVIDER,
        "name": TOOL_NAME,
        "arguments": {
            "title": title,
            "content": content,
            "folder_id": folder_id,
        },
        # 扁平字段兼容部分桥接实现
        "title": title,
        "content": content,
        "folder_id": folder_id,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "job-application-email-skill/notes_create_note",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    note_id = ""
    try:
        parsed = json.loads(body) if body else {}
        note_id = str(
            parsed.get("id")
            or parsed.get("note_id")
            or (parsed.get("result") or {}).get("id")
            or ""
        )
    except json.JSONDecodeError:
        parsed = {}
    return NoteResult(
        True,
        TOOL_NAME,
        PROVIDER,
        note_id or "remote",
        url,
        body[:500] or f"{TOOL_NAME} ok",
    )


def _local_notepad(title: str, content: str, folder_id: str, notes_dir: Path) -> NoteResult:
    base = notes_dir
    if folder_id:
        base = base / _safe_filename(folder_id)
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = base / f"{stamp}_{_safe_filename(title)}.txt"
    header = (
        f"tool: {TOOL_NAME}\n"
        f"provider: {PROVIDER}\n"
        f"folder_id: {folder_id or '(empty)'}\n"
        f"{'=' * 40}\n"
        f"{title}\n"
        f"{'=' * 40}\n\n"
    )
    path.write_text(header + (content or "") + "\n", encoding="utf-8")
    return NoteResult(
        True,
        TOOL_NAME,
        "local_notepad_fallback",
        path.stem,
        str(path),
        "DroiClaw MCP unavailable in this environment; wrote local notepad for demo",
    )


def notes_create_note(
    title: str,
    content: str,
    folder_id: str = "",
    *,
    notes_dir: str | Path | None = None,
) -> NoteResult:
    """
    创建笔记 —— 对应能力手册：notes_create_note(title, content, folder_id)
    """
    title = (title or "").strip() or "未命名笔记"
    content = content if content is not None else ""
    folder_id = (folder_id or "").strip()

    mcp_url = (
        os.environ.get("DROICLAW_MCP_URL", "").strip()
        or os.environ.get("JOB_NOTES_WEBHOOK_URL", "").strip()
    )
    if mcp_url:
        try:
            return _post_mcp(mcp_url, title, content, folder_id)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # 远程失败仍回退本地，保证演示不中断
            result = _local_notepad(
                title,
                content,
                folder_id,
                Path(notes_dir or os.path.expanduser("~/.job-outreach/notes")).expanduser(),
            )
            result.message = f"remote {TOOL_NAME} failed ({exc}); {result.message}"
            return result

    return _local_notepad(
        title,
        content,
        folder_id,
        Path(notes_dir or os.path.expanduser("~/.job-outreach/notes")).expanduser(),
    )


# 别名：与手册中文「创建笔记 create_note」对应（完整名为 notes_create_note）
create_note = notes_create_note


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"DroiClaw MCP tool: {TOOL_NAME} (title, content, folder_id)"
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", default="")
    parser.add_argument("--content-file", help="从文件读取 content")
    parser.add_argument("--folder-id", default="", dest="folder_id")
    parser.add_argument("--notes-dir", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    content = args.content
    if args.content_file:
        content = Path(args.content_file).expanduser().read_text(encoding="utf-8")

    result = notes_create_note(
        args.title,
        content,
        args.folder_id,
        notes_dir=args.notes_dir or None,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        status = "OK" if result.ok else "FAIL"
        print(
            f"{status} tool={result.tool} provider={result.provider} "
            f"id={result.note_id} path={result.path_or_uri} msg={result.message}"
        )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
