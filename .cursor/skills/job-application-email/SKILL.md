---
name: job-application-email
description: 轮询校招官网采集全新岗位后，调用 DroiClaw MCP 工具 notes_create_note（provider: notes；参数 title/content/folder_id）写入手机便签。云端无 MCP 时回退本地记事本以便演示。当用户提到岗位速递、便签、notes_create_note、记事本时使用。
disable-model-invocation: true
---

# Job Application Email（新岗位 → DroiClaw `notes_create_note`）

## 必须调用的 MCP Tool（能力手册）

来源：[references/droiclaw-mcp-handbook.md](references/droiclaw-mcp-handbook.md)

| 项 | 值 |
|----|-----|
| Provider | `notes`（便签 / 待办） |
| Tool 全名 | **`notes_create_note`**（命名规则 `{provider}_{tool_name}`） |
| 中文 | 创建笔记 |
| 参数 | `title` + `content` + `folder_id` |

> 手册原文：创建笔记 `create_note` —— 参数 `title` + `content` + `folder_id`  
> Skill / 脚本中必须使用完整 Tool 名 **`notes_create_note`**，禁止自造英文名。

### Agent 执行时（手机 DroiClaw 环境）

对每条（或每批）新岗位调用：

```text
notes_create_note(
  title="<笔记标题>",
  content="<官网链接 + 职位链接 + 职位内容>",
  folder_id="<配置中的 folder_id，默认 job-digest>"
)
```

缺 `folder_id` 时先问用户或使用配置默认值；调用失败须如实告知，不能假装成功。  
**不能**设计删除笔记（`delete_note` 未开放）。

### 脚本入口（本仓库）

```bash
python scripts/create_note.py --title "标题" --content "正文" --folder-id job-digest
# 内部函数：notes_create_note(title, content, folder_id)
python scripts/run_daily.py --config ~/.job-outreach/config.yaml
```

若设置 `DROICLAW_MCP_URL`（或 `JOB_NOTES_WEBHOOK_URL`），脚本会 POST：

```json
{
  "tool": "notes_create_note",
  "provider": "notes",
  "arguments": { "title": "...", "content": "...", "folder_id": "..." }
}
```

无 MCP 时回退本地 `~/.job-outreach/notes/<folder_id>/*.txt`（仅演示）。

## 产品规则（不变）

1. 九家公司官网监控  
2. 有新岗位立刻处理（轮询，无固定整点）  
3. 关键词：Java / 后端 / 实习 / 校招 / Agent / 开发  
4. 只推全新，宁少勿多  
5. 笔记内容含官网链接、职位链接、职位内容  
6. 关闭外投简历；默认不走 SMTP

## IDEA 打开

| 字段 | 值 |
|------|-----|
| **URL** | `https://github.com/ShaoTiC/UserAPI1.git` |
| **Directory** | 本地空目录，例如 `C:\Users\你的用户名\IdeaProjects\UserAPI1` |
| 分支 | `cursor/job-application-email-skill-1d7d` |
| Skill 路径 | `<Directory>/.cursor/skills/job-application-email/` |

macOS Directory 示例：`/Users/你的用户名/IdeaProjects/UserAPI1`

## 快速演示（无手机 MCP）

```bash
cd .cursor/skills/job-application-email
pip install -r requirements.txt
# config: notify_channel=notes；companies 可用 assets/fixtures/demo_companies.csv
python scripts/run_daily.py --config ~/.job-outreach/config.yaml
ls ~/.job-outreach/notes/job-digest/
```

## 文档

- [DEPLOY.md](DEPLOY.md)
- [docs/EXCEPTION_HANDLING.md](docs/EXCEPTION_HANDLING.md)
- [references/droiclaw-mcp-handbook.md](references/droiclaw-mcp-handbook.md)
