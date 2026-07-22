# 求职邮件审核标准（Review Standards）

发送前由 Agent / 人工按本标准核对。任一项 **阻断项** 不通过则禁止发送。

## 1. 内容合规（阻断）

| 检查项 | 标准 | 不通过处理 |
|--------|------|------------|
| 自我介绍 | 必须与固定原文完全一致（含标点） | `INTRO_MISMATCH`，恢复 `assets/self_intro.txt` |
| 虚假承诺 | 不得添加未经验证的薪资、Offer、内部推荐承诺 | 删除后重审 |
| 敏感信息 | 正文不出现身份证号、银行卡、超额隐私 | 删除后重审 |
| 简历一致性 | 附件姓名/学校/方向与主题一致 | 更正附件或主题 |

**固定自我介绍原文：**

```text
我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,有后端实习经历,独立开发智能体协作平台。
```

## 2. 收件人质量（阻断 / 警告）

| 检查项 | 标准 | 级别 |
|--------|------|------|
| 邮箱格式 | RFC 基本格式，含 `@` 与合法域名 | 阻断 |
| 官方渠道 | 优先官网 HR / campus / jobs 邮箱；避免个人随意邮箱 | 警告 |
| 一次性邮箱 | mailinator 等临时域 | 阻断（`blocked_domains`） |
| 重复投递 | 同一 `company_id|email` 已 `sent` 默认不重发 | 阻断（除非 `--force`） |

## 3. 发送节奏（阻断）

| 检查项 | 建议默认值 | 说明 |
|--------|------------|------|
| 工作日 | 周一至周五 | 周末默认跳过 |
| 时段 | 09:30 / 14:30（`Asia/Shanghai`） | 与 cron / scheduler 对齐 |
| 每 slot 批量 | 3–10 封 | `schedule.batch_size` |
| 封间间隔 | ≥ 8 秒 | `mail.min_interval_sec` |
| 日上限 | ≤ 40 封（视邮箱服务商而定） | `security.daily_send_limit` |

超过日上限必须停止，次日再发。

## 4. 技术与安全（阻断）

- 简历必须为 PDF，且 ≤ `mail.max_attachment_mb`（默认 5MB）
- SMTP 授权码 / API Key 不得提交到 Git
- `check_security.py` 必须 exit 0
- `AUTH_FAILED` 立即熔断整批
- 生产环境禁止 `--skip-security`

## 5. 主题与附件命名（建议）

- 主题默认：`求职-Java开发实习生-邵俊凯-东北农业大学`
- 附件默认：`邵俊凯-Java开发实习生-简历.pdf`
- 避免过度营销符号（多个 `!!!`、全大写英文标题）

## 6. 审核输出格式

```text
Review: PASS|FAIL
Blockers:
- ...
Warnings:
- ...
Approved recipients: N
```

## 7. 与失败码映射

审核不通过时，优先使用与 `SKILL.md` 一致的失败码：`INTRO_MISMATCH`、`RESUME_MISSING`、`SECURITY_BLOCKED`、`INVALID_EMAIL`、`SECRET_IN_FILE`（警告）等，便于报告聚合与重试决策。
