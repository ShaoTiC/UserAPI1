---
name: job-application-email
description: 在工作日固定时段（默认上午 9:30、下午 14:30）向目标公司邮箱批量发送求职邮件（简历附件 + 固定自我介绍）。适用于投递、冷邮件、日更求职触达；当用户提到求职邮件、批量投递、定时发简历、公司邮箱列表或 job outreach 时使用本 skill。
disable-model-invocation: true
---

# Job Application Email（求职定时投递）

面向求职者的可复用投递工作流：读取公司邮箱列表 → 安全检查 → 组装邮件（固定自我介绍 + 简历附件）→ 调用邮件 API/SMTP 发送 → 记录结果与重试。

## 何时使用

- 用户要求按工作日固定时间向目标公司发求职邮件
- 用户已有公司官网/邮箱列表，需要批量或定时投递
- 用户要求校验投递安全性、生成投递报告、排查发送失败

## 目录结构

```text
job-application-email/
├── SKILL.md
├── scripts/
│   ├── check_security.py      # 发送前安全与合规检查（必需）
│   ├── send_batch.py          # 批量发送主入口
│   ├── schedule_runner.py     # 工作日 9:30 / 14:30 调度入口
│   └── lib_mail.py            # SMTP / HTTP API 发送实现
├── references/
│   └── review_standards.md    # 投递内容与合规审核标准
├── assets/
│   ├── report_template.md     # 投递报告模板
│   ├── config.example.yaml    # 配置样例
│   ├── companies.example.csv  # 公司邮箱列表示例
│   ├── self_intro.txt         # 固定自我介绍
│   └── resume/                # 放置简历 PDF（用户自行放入）
└── tests/
    └── test_cases.md          # 测试用例
```

## 固定自我介绍（verbatim）

邮件正文必须使用以下固定文案，**不得改写、增删或润色**：

> 我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,有后端实习经历,独立开发智能体协作平台。

## 快速开始

### 1. 准备配置与资产

1. 复制 `assets/config.example.yaml` → 本地私有路径（如 `~/.job-outreach/config.yaml`），填入 SMTP 或邮件 API 凭证。
2. 复制 `assets/companies.example.csv` → 实际公司列表文件，填入目标邮箱。
3. 将简历 PDF 放到 `assets/resume/`（或在 config 中指定绝对路径）。
4. **禁止**把真实 SMTP 密码、API Key 写入仓库；使用环境变量或本地配置文件。

### 2. 发送前安全检查（必须）

```bash
python scripts/check_security.py \
  --config ~/.job-outreach/config.yaml \
  --companies ~/.job-outreach/companies.csv \
  --resume /path/to/resume.pdf
```

退出码 `0` 才允许继续发送；非 0 必须修复后重试。

### 3. 立即试发（单封 dry-run / 实发）

```bash
# 仅预览，不真正发送
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --dry-run --limit 1

# 实发 1 封到列表中下一条未发送记录
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --limit 1
```

### 4. 工作日定时任务（9:30 / 14:30）

```bash
# 前台运行调度器（适合长期开机的本机 / 服务器）
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml

# 或使用 cron（推荐生产环境）
# 工作日 9:30
30 9 * * 1-5 cd /path/to/job-application-email && python scripts/send_batch.py --config ~/.job-outreach/config.yaml --slot morning
# 工作日 14:30
30 14 * * 1-5 cd /path/to/job-application-email && python scripts/send_batch.py --config ~/.job-outreach/config.yaml --slot afternoon
```

时区默认 `Asia/Shanghai`，可在 config 的 `schedule.timezone` 覆盖。

## Agent 执行清单

复制并跟踪：

```text
Task Progress:
- [ ] 确认 config / companies / resume / self_intro 路径
- [ ] 阅读 references/review_standards.md 并核对邮件主题与正文
- [ ] 运行 check_security.py，确认 exit 0
- [ ] dry-run 1 封，核对收件人、主题、附件名
- [ ] 小批量实发（limit=1~3），确认对方邮箱可收
- [ ] 配置 cron 或 schedule_runner（工作日 9:30 / 14:30）
- [ ] 按 assets/report_template.md 输出投递报告
- [ ] 对失败项按「失败场景与排查」执行重试或人工介入
```

## 邮件组装规范

| 字段 | 规则 |
|------|------|
| To | 来自公司列表 `email` 列；每封一公司 |
| Subject | 默认：`求职-Java开发实习生-邵俊凯-东北农业大学`（可用 config 覆盖） |
| Body | 固定自我介绍全文；可追加一行礼貌收尾（见 config `email.closing`，可为空） |
| Attachment | 简历 PDF，文件名建议：`邵俊凯-Java开发实习生-简历.pdf` |
| From | config 中的发件人；须与 SMTP/API 账号一致 |

每次时段默认发送数量由 `schedule.batch_size` 控制（建议 3~10），避免短时间海量投递触发反垃圾。

## 状态与幂等

- 状态文件默认：`~/.job-outreach/state.json`（可配置）
- 同一 `company_id` + `email` 在成功后标记 `sent`，默认不再重发
- 失败标记 `failed` + `last_error`，进入重试队列
- 使用 `--force` 才允许对已 `sent` 记录重发

## 外部 API / SMTP

本 skill 支持两种发送后端（config `mail.provider`）：

1. **smtp**（默认）：标准 SMTP（QQ / 163 / Gmail / 企业邮）
2. **http_api**：通用 HTTP JSON API（如 Resend / SendGrid 兼容适配；见 `lib_mail.py`）

凭证优先从环境变量读取：

| 变量 | 用途 |
|------|------|
| `JOB_OUTREACH_SMTP_PASSWORD` | SMTP 密码 / 授权码 |
| `JOB_OUTREACH_API_KEY` | HTTP API Key |
| `JOB_OUTREACH_CONFIG` | 覆盖默认 config 路径 |

## 失败场景、排查与重试

详见下表；脚本内置指数退避重试（默认最多 3 次：2s → 4s → 8s）。

| 失败码 / 现象 | 可能原因 | 排查步骤 | 重试策略 |
|---------------|----------|----------|----------|
| `CONFIG_INVALID` | YAML 缺字段、路径错误 | 对照 `config.example.yaml`；跑 `check_security.py` | 不自动重试；修复配置后人工重跑 |
| `RESUME_MISSING` | 简历文件不存在或非 PDF | 检查 `resume.path`；确认扩展名为 `.pdf` | 不自动重试 |
| `INTRO_MISMATCH` | 自我介绍被改动 | 恢复 `assets/self_intro.txt` 为固定原文 | 不自动重试 |
| `SECURITY_BLOCKED` | 域名黑名单、日限额、可疑附件 | 读 `check_security.py` 输出；见 [review_standards.md](references/review_standards.md) | 不自动重试 |
| `AUTH_FAILED` (535/401) | 授权码错误、未开 SMTP、API Key 失效 | 重新生成授权码；确认环境变量；检查 From 是否匹配 | 最多 1 次立即重试；仍失败则停止整批 |
| `RATE_LIMITED` (429/550 freq) | 发送过快 / 日限额 | 增大 `mail.min_interval_sec`；减小 `batch_size` | 退避重试 3 次；仍失败则本 slot 剩余改 `deferred` |
| `TIMEOUT` / 网络错误 | DNS、防火墙、代理 | `ping`/`curl` 测连通；检查代理与 465/587 端口 | 指数退避 3 次 |
| `INVALID_RECIPIENT` (550/551) | 邮箱不存在或拒收 | 人工核实官网招聘邮箱；更新 CSV | 不重试该条；标记 `invalid` |
| `ATTACHMENT_REJECTED` | 附件过大或类型拦截 | 压缩/精简 PDF；确认 `< mail.max_attachment_mb` | 不自动重试 |
| `SPAM_REJECTED` | 内容被判垃圾邮件 | 确认只用固定介绍；换企业邮发送；降低频率 | 本 slot 停止；次日再试 |
| `PARTIAL_BATCH_FAIL` | 批次中部分成功 | 查 `state.json`；只对 `failed`/`deferred` 重跑 | `send_batch.py --retry-failed` |
| `NOT_WORKDAY` / `WRONG_SLOT` | 非工作日或非调度窗口 | 确认时区与 cron；节假日可手动 `--force-schedule` | 跳过，不记失败 |
| `STATE_CORRUPT` | state.json 损坏 | 从 `state.json.bak` 恢复；或备份后重建 | 不自动重试 |

### 重试机制（实现约定）

1. **单封瞬时重试**：网络/超时/429 → 最多 `mail.max_retries`（默认 3），间隔 `base * 2^n` 秒。
2. **认证失败熔断**：`AUTH_FAILED` 立即终止本批次，避免密码错误刷爆。
3. **跨时段重试**：`failed`/`deferred` 进入下一 slot（下午或下一工作日上午）由 `--retry-failed` 或调度器自动拾取。
4. **人工门禁**：连续 5 封失败或安全检查失败 → 写入报告并要求人工确认后再继续。
5. **幂等**：成功写入 state 后，默认跳过，防止 cron 重复触发导致重复投递。

## 输出报告

发送结束后，按 [assets/report_template.md](assets/report_template.md) 生成当日报告，保存到 config 中的 `report.dir`。

## 审核标准

发送前对照 [references/review_standards.md](references/review_standards.md)。

## 测试

完整用例见 [tests/test_cases.md](tests/test_cases.md)。最低验收：

1. `check_security.py` 对缺简历返回非 0
2. dry-run 不产生真实发送、不改 sent 状态（可写 preview 日志）
3. 固定自我介绍字节级一致
4. 非工作日 `schedule_runner` 跳过
5. 模拟 429 时触发退避重试

## 需要用户确认 / 可调整项（反馈清单）

若以下信息与你的实际环境不符，请告知以便调整 skill：

1. **邮件通道**：当前默认 SMTP；若你固定用某云 API（Resend / SendGrid / 阿里云邮件推送），请给出 API 文档或样例请求。
2. **公司列表格式**：默认 CSV（`company_id,company_name,website,email,note`）；若已是 JSON/Excel，可增加适配器。
3. **简历文件**：请将最终 PDF 放入 `assets/resume/` 或提供路径；仓库内不强制提交真实简历。
4. **发件身份**：默认主题含「邵俊凯」；若姓名/意向岗位变更，改 config 即可。
5. **法定节假日**：当前仅跳过周六日；若需跳过中国法定假日，可接入节假日 API。
6. **每 slot 发送量、最小间隔、日上限**：见 config，请按目标邮箱服务商限制调整。

## 依赖

- Python 3.10+
- 标准库为主；可选 `PyYAML`（配置）、`requests`（HTTP API）

```bash
pip install pyyaml requests
```
