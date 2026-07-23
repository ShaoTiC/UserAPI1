---
name: job-application-email
description: 工作日从目标公司官网/RSS/JSON 采集新发布招聘岗位，汇总约 10 条发送到用户自己的邮箱（默认 3461630168@qq.com），帮助尽快获知岗位并及时投递。可选保留向外投递简历能力。当用户提到招聘速递、岗位采集、官网新岗位、每日岗位摘要、求职信息聚合时使用本 skill。
disable-model-invocation: true
---

# Job Application Email（招聘速递 + 可选外投）

## 主功能（默认 `mode: digest`）

工作日定时从配置的公司招聘页采集**新岗位** → 按关键词过滤 → 去重 → 汇总约 **10** 条 → 发送到用户邮箱 **3461630168@qq.com**。

目标：替用户节省信息收集时间，尽快收到可投递岗位。

## 可选功能（`mode: outreach`）

保留原「向公司邮箱发送简历 + 固定自我介绍」能力，默认关闭（`schedule.enable_outreach_slots: false`）。

## 何时使用

- 用户要每日接收官网新岗位摘要
- 用户已有公司官网/招聘页列表，需要自动采集与去重
- 用户提到招聘速递、岗位聚合、及时投递
- （可选）仍需批量向外发求职邮件

## 目录结构

```text
job-application-email/
├── SKILL.md
├── DEPLOY.md
├── scripts/
│   ├── check_security.py      # 安全检查（digest / outreach）
│   ├── job_sources.py         # RSS / HTML正则 / JSON / fixture 采集
│   ├── collect_jobs.py        # 采集入口
│   ├── send_digest.py         # 发送岗位摘要到用户邮箱
│   ├── run_daily.py           # 每日流水线：采集 → 摘要
│   ├── schedule_runner.py     # 工作日定时（默认 09:00 摘要）
│   ├── send_batch.py          # （可选）向外投递简历
│   └── lib_mail.py            # SMTP / HTTP API
├── references/
│   └── review_standards.md
├── assets/
│   ├── report_template.md
│   ├── config.example.yaml
│   ├── companies.example.csv
│   ├── fixtures/              # 本地演示岗位数据
│   ├── self_intro.txt         # outreach 用
│   └── resume/
└── tests/
```

## 部署文档

完整步骤见 [DEPLOY.md](DEPLOY.md)。

## 快速开始（digest）

### 1. 配置

1. 复制 `assets/config.example.yaml` → `~/.job-outreach/config.yaml`
2. 复制 `assets/companies.example.csv` → `~/.job-outreach/companies.csv`，填入真实 `careers_url` / `source_type`
3. 设置 `digest.to_email: 3461630168@qq.com`（示例已默认）
4. `export JOB_OUTREACH_SMTP_PASSWORD='授权码'`

### 2. 安全检查

```bash
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode digest
```

### 3. 试跑（本地 fixture 可不联网）

```bash
# 公司列表可先指向 skill 内 assets/companies.example.csv（fixture 演示）
python scripts/run_daily.py --config ~/.job-outreach/config.yaml --dry-run --force-schedule --limit 10
```

### 4. 实发摘要到自己邮箱

```bash
python scripts/run_daily.py --config ~/.job-outreach/config.yaml --force-schedule --limit 10
```

### 5. 定时（工作日 09:00）

```bash
# 前台
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml

# cron 推荐
0 9 * * 1-5 cd /path/to/job-application-email && . .venv/bin/activate && . ~/.job-outreach/env.sh && python scripts/run_daily.py --config ~/.job-outreach/config.yaml >> ~/.job-outreach/cron.log 2>&1
```

## Agent 执行清单

```text
Task Progress:
- [ ] 确认 mode=digest，digest.to_email 正确
- [ ] 确认 companies.csv 含 careers_url + source_type
- [ ] check_security.py --mode digest → PASS
- [ ] collect_jobs.py 能拉到岗位（或 fixture 演示）
- [ ] send_digest.py --dry-run 预览约 10 条
- [ ] 实发一封到 3461630168@qq.com 并查收
- [ ] 配置工作日 digest_time 定时任务
- [ ] 按报告检查失败源并重试
```

## 采集源类型

| source_type | careers_url | 额外字段 | 说明 |
|-------------|-------------|---------|------|
| `fixture` | 相对 skill 的 JSON 路径 | — | 本地演示/测试 |
| `rss` | RSS/Atom URL | — | 优先推荐 |
| `html_regex` | 招聘列表页 URL | `item_regex`（命名组 `title`/`url`） | 静态 HTML |
| `json` | JSON API URL | 可选 `json_list_key` 等 | 结构化接口 |

关键词：`digest.keywords` 全局过滤；CSV `keywords` 列用 `|` 分隔可覆盖单行。

## 去重与配额

- `state.json` 中 `seen_jobs` 记录已通知岗位，避免重复推送
- `digest.daily_job_limit` 默认 10；优先全新岗位，不足时用当日仍匹配的已知岗位补齐
- 同一自然日默认只发一封摘要（`--force` 可重发）

## 邮件内容

发往 `digest.to_email`，主题默认：`【每日招聘速递】{date} · {count} 条新岗位`  
正文含：公司、岗位名、链接、地点/时间/摘要（若有）。

## 失败场景、排查与重试

| 失败码 / 现象 | 可能原因 | 排查 | 重试 |
|---------------|----------|------|------|
| `CONFIG_INVALID` | 缺 to_email / SMTP 字段 | 对照 config.example.yaml | 修配置后重跑 |
| `COMPANIES_SCHEMA` | CSV 缺 careers_url/source_type | 补齐列 | 不自动重试 |
| `CAREERS_URL_MISSING` | 某行无招聘页 | 补 URL | 跳过该行 |
| `SOURCE_TYPE_INVALID` | 类型不支持 | 改为 rss/html_regex/json/fixture | — |
| 采集 `URLError`/`HTTPError` | 官网不可达、反爬 | 换 RSS/API；增大 timeout；检查 UA | 下一日再采；本源记入 errors |
| `JOBS_CACHE_MISSING` | 未先采集 | 先跑 collect_jobs / run_daily | — |
| `NO_JOBS` | 无匹配关键词 | 放宽 keywords；检查源 | 不发信（正常） |
| `ALREADY_SENT` | 今日已发 | 等明日或 `--force` | — |
| `AUTH_FAILED` | 授权码错误 | 重做 QQ 授权码 | 熔断，修好再发 |
| `TIMEOUT` / `RATE_LIMITED` | 网络或限流 | 退避（mail.max_retries） | 指数退避 3 次 |
| 页面为空但浏览器有数据 | **JS 渲染站点** | 改用 RSS/官方 API；或后续接入浏览器采集 | 需人工调整源 |

### 重试机制

1. 邮件发送：与既有 `lib_mail` 一致，瞬时失败指数退避最多 3 次。
2. 单公司采集失败：记入当日 cache `errors`，不阻断其他公司。
3. 摘要发送失败：不写入 `digest_daily` 成功标记，可直接重跑 `send_digest.py`。
4. 已成功摘要中的岗位写入 `seen_jobs`，次日不会重复推送同一 `job_id`。

## 可选：outreach 外投

固定自我介绍（不得改写）：

> 我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,有后端实习经历,独立开发智能体协作平台。

```bash
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode outreach
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --dry-run --limit 1
```

详见历史外投流程与 `assets/self_intro.txt`。

## 审核标准

见 [references/review_standards.md](references/review_standards.md)。

## 测试

见 [tests/test_cases.md](tests/test_cases.md)。最低验收：

1. fixture 源可采集并过滤关键词
2. dry-run 摘要不改 `digest_daily`
3. `daily_job_limit=10` 截断生效
4. 重复 `job_id` 第二次不再作为 new
5. digest 模式不要求简历文件存在

## 需要你确认的点（请反馈）

1. **公司清单**：请提供真实官网招聘页 URL，并尽量标注是否有 RSS/JSON；纯 JS 页面当前 `html_regex` 可能采不到。
2. **发送时刻**：默认工作日 **09:00** 一封；是否改成 09:30 或早晚两封？
3. **关键词**：默认 Java/后端/实习/校招/Agent/开发，是否要增删？
4. **不足 10 条时**：当前用「已知但仍匹配」岗位补齐；是否改为「宁少勿补」只发全新？
5. **是否还要保留自动外投简历**：默认关闭，需要可开 `enable_outreach_slots`。

## 依赖

```bash
pip install pyyaml requests
```

Python 3.10+；采集以标准库为主（urllib / xml / json / re）。
