# 审核标准（Review Standards）

默认审核对象为 **digest（岗位摘要）**；outreach 外投规则保留在后半部分。

## A. Digest 模式（主流程）

### A1. 收件与配额（阻断）

| 检查项 | 标准 |
|--------|------|
| 收件人 | 必须是用户本人邮箱（默认 `3461630168@qq.com`） |
| 每日条数 | 约 10 条，`daily_job_limit` ∈ [1, 50] |
| 重复推送 | 同一 `job_id` 已通知则不应再作为「新岗位」主推 |
| 同日重复邮件 | 无 `--force` 时每日仅一封摘要 |

### A2. 内容质量（警告 / 阻断）

| 检查项 | 标准 | 级别 |
|--------|------|------|
| 链接可点 | 每条含 http(s) URL | 阻断单条 |
| 关键词相关 | 标题命中配置关键词（或行级 keywords） | 警告（过宽易噪声） |
| 无虚假「内推保过」等话术 | 摘要仅转述公开岗位信息 | 阻断 |
| 来源可追溯 | 标明公司名与链接 | 阻断 |

### A3. 采集源（阻断）

- CSV 含 `company_id,company_name,careers_url,source_type`
- `html_regex` 必须有合法 `item_regex`（`title`/`url` 命名组）
- 禁止把 SMTP 授权码写入仓库

### A4. 审核输出

```text
Review: PASS|FAIL
Mode: digest
Blockers:
- ...
Warnings:
- ...
Jobs selected: N
Recipient: ...
```

## B. Outreach 模式（可选外投）

### B1. 内容合规（阻断）

| 检查项 | 标准 |
|--------|------|
| 自我介绍 | 必须与固定原文完全一致 |
| 简历 | PDF 存在且不超过大小上限 |
| 敏感信息 | 正文不出现身份证号等 |

**固定自我介绍原文：**

```text
我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,有后端实习经历,独立开发智能体协作平台。
```

### B2. 发送节奏

工作日、时段、batch_size、日上限与旧版一致；见 `SKILL.md` outreach 节。
