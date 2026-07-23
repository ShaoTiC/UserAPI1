---
name: job-application-email
description: 持续轮询目标公司校招官网，发现匹配关键词的全新岗位后调用 create_note（provider: notes）写入便签/记事本；便于演示，无需 SMTP。也可选 email。当用户提到招聘速递、岗位便签、create_note、记事本归档时使用本 skill。
disable-model-invocation: true
---

# Job Application Email（新岗位 → 便签 create_note）

## 当前主路径

1. 采集九家公司官网新岗位  
2. 只保留全新匹配岗位  
3. 调用 **create_note(title, content, folder_id)** 写入便签/记事本  
4. 若无 notes MCP，则回退为本地 `.txt` 记事本文件（保证可演示）

## 便签 API（provider: notes）

```text
创建笔记 create_note
参数：
  - title: string
  - content: string
  - folder_id: string
```

```bash
python scripts/create_note.py --title "标题" --content "正文" --folder-id job-digest
python scripts/run_daily.py --config ~/.job-outreach/config.yaml
```

Agent 在 Cursor 桌面若已连接 notes MCP：对同样参数调用 MCP `create_note`；脚本侧用本地记事本 / `JOB_NOTES_WEBHOOK_URL` 作为可靠回退。

## IDEA

- URL：`https://github.com/ShaoTiC/UserAPI1.git`
- Directory：如 `C:\Users\你\IdeaProjects\UserAPI1`
- 分支：`cursor/job-application-email-skill-1d7d`
- Skill：`<Directory>/.cursor/skills/job-application-email/`

## 快速演示（无需邮箱）

```bash
cd .cursor/skills/job-application-email
pip install -r requirements.txt
# 使用 assets/config.example.yaml，notify_channel: notes
# companies 可先指向 assets/fixtures/demo_companies.csv
python scripts/run_daily.py --config ~/.job-outreach/config.yaml
# 查看记事本
ls ~/.job-outreach/notes/job-digest/
```

## 文档

- [DEPLOY.md](DEPLOY.md)
- [docs/EXCEPTION_HANDLING.md](docs/EXCEPTION_HANDLING.md)

## 说明

- `notify_channel: notes` 时不需要 SMTP  
- 外投简历保持关闭  
- 可选环境变量 `JOB_NOTES_WEBHOOK_URL` 转发 create_note  
