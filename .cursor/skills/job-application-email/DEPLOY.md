# 求职 Skill 部署与运行指南（DEPLOY）

本 skill **默认用途**：工作日从目标公司官网采集新招聘岗位，汇总约 **10** 条，发送到你的邮箱 **3461630168@qq.com**，便于尽快投递。

可选：开启 `outreach` 模式向外投递简历（旧功能保留）。

仓库：https://github.com/ShaoTiC/UserAPI1  
分支：`cursor/job-application-email-skill-1d7d`  
路径：`.cursor/skills/job-application-email/`

---

## 1. 前置条件

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| 发件邮箱 | QQ SMTP 授权码（示例发件人 `3461630168@qq.com`） |
| 收件邮箱 | 默认 `3461630168@qq.com`（可在 config 修改） |
| 公司源 | `careers_url` + `source_type`（rss / html_regex / json / fixture） |
| 机器 | 工作日定时可运行（本机或云主机） |

> 限制：大量招聘站为前端渲染，静态 `html_regex` 可能失败；**优先找 RSS / 官方 JSON API**。

---

## 2. 获取代码与安装

```bash
git clone https://github.com/ShaoTiC/UserAPI1.git
cd UserAPI1
git checkout cursor/job-application-email-skill-1d7d
cd .cursor/skills/job-application-email

python3 -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python tests/run_smoke.py          # 期望 SMOKE PASS
```

---

## 3. 开通 QQ SMTP

1. https://mail.qq.com → 设置 → 账户 → 开启 SMTP  
2. 生成授权码  
3. 不要写入 Git：

```bash
export JOB_OUTREACH_SMTP_PASSWORD='你的授权码'
export JOB_OUTREACH_CONFIG="$HOME/.job-outreach/config.yaml"
```

---

## 4. 本地配置

```bash
mkdir -p ~/.job-outreach/reports ~/.job-outreach/cache
cp assets/config.example.yaml ~/.job-outreach/config.yaml
cp assets/companies.example.csv ~/.job-outreach/companies.csv
```

编辑 `~/.job-outreach/config.yaml` 确认：

```yaml
mode: digest
mail:
  from_email: "3461630168@qq.com"
  smtp_username: "3461630168@qq.com"
digest:
  to_email: "3461630168@qq.com"
  daily_job_limit: 10
schedule:
  timezone: "Asia/Shanghai"
  digest_time: "09:00"
  enable_outreach_slots: false
paths:
  companies: "~/.job-outreach/companies.csv"
  state: "~/.job-outreach/state.json"
  jobs_cache: "~/.job-outreach/cache"
```

### companies.csv（digest）

必填列：`company_id,company_name,careers_url,source_type`

演示（不联网，用仓库 fixture）：

```csv
company_id,company_name,website,careers_url,source_type,item_regex,keywords,email,note
demo001,示例科技A,,assets/fixtures/demo_jobs_a.json,fixture,,,Java|后端|实习,,
demo002,示例科技B,,assets/fixtures/demo_jobs_b.json,fixture,,,Java|Agent|校招,,
```

真实站点示例：

```csv
acme001,某某公司,https://www.acme.com,https://www.acme.com/jobs/rss,rss,,,Java|后端,,
```

`html_regex` 必须提供 `item_regex`，且含命名组 `title`、`url`。

若 `paths.companies` 指向 `~/.job-outreach/companies.csv` 且使用 fixture，请把 `careers_url` 写成 skill 内绝对路径，或把 `companies` 暂时改为 skill 下的 `assets/companies.example.csv`。

---

## 5. 验收四步

在 `$SKILL_ROOT` 且已 `source .venv/bin/activate`：

```bash
# A. 安全检查
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode digest

# B. 仅采集
python scripts/collect_jobs.py --config ~/.job-outreach/config.yaml

# C. Dry-run 摘要（不真发）
python scripts/send_digest.py --config ~/.job-outreach/config.yaml --dry-run --limit 10

# D. 一键流水线实发
python scripts/run_daily.py --config ~/.job-outreach/config.yaml --force-schedule --limit 10
```

然后登录 `3461630168@qq.com` 查收「每日招聘速递」。

---

## 6. 定时任务（工作日 09:00）

### cron

`~/.job-outreach/env.sh`：

```bash
export JOB_OUTREACH_SMTP_PASSWORD='你的授权码'
export JOB_OUTREACH_CONFIG="$HOME/.job-outreach/config.yaml"
```

```cron
0 9 * * 1-5 cd /绝对路径/job-application-email && . .venv/bin/activate && . $HOME/.job-outreach/env.sh && python scripts/run_daily.py --config $HOME/.job-outreach/config.yaml >> $HOME/.job-outreach/cron.log 2>&1
```

### 前台调度器

```bash
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
```

### Windows

用任务计划程序每天一至五 9:00 运行 bat，内容调用 `python scripts\run_daily.py ...`。

---

## 7. 日常运维

```bash
# 看采集缓存
ls ~/.job-outreach/cache/

# 看是否已通知过的岗位
cat ~/.job-outreach/state.json

# 看报告
ls ~/.job-outreach/reports/

# 今日已发仍想重发
python scripts/send_digest.py --config ~/.job-outreach/config.yaml --force
```

建议节奏：`daily_job_limit` 保持 8–12；关键词过严会导致经常 `NO_JOBS`。

---

## 8. 可选：outreach 外投简历

1. `config.mode` 可保持 digest；外投用 CLI `--mode outreach`  
2. 准备 `resume.pdf` 与合法公司 `email` 列  
3. `schedule.enable_outreach_slots: true` 可恢复 09:30/14:30 外投  
4. 固定自我介绍见 `assets/self_intro.txt`（不得改写）

```bash
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --dry-run --limit 1
```

---

## 9. 故障排查

| 现象 | 处理 |
|------|------|
| 采集为空 | 检查关键词；对 JS 站改用 RSS/API |
| `ITEM_REGEX_MISSING` | html_regex 行补 `item_regex` |
| `AUTH_FAILED` | 重做授权码 |
| `ALREADY_SENT` | 明日再发或 `--force` |
| 邮件进垃圾箱 | 降低频率；检查主题/发件人 |
| fixture 找不到 | `careers_url` 相对 skill 根目录，或用绝对路径 |

更多失败码见 `SKILL.md`。

---

## 10. Checklist

```text
[ ] clone / checkout skill 分支
[ ] venv + pip + smoke PASS
[ ] SMTP 授权码环境变量
[ ] config 中 digest.to_email = 3461630168@qq.com
[ ] companies.csv 配置采集源（先 fixture 再真实站）
[ ] check_security digest PASS
[ ] dry-run 摘要预览约 10 条
[ ] 实发到自己邮箱成功
[ ] cron 工作日 09:00
[ ] 次日确认去重生效（不重复推同一岗位）
```

---

## 附录：常用命令

```bash
python scripts/run_daily.py --config ~/.job-outreach/config.yaml --force-schedule
python scripts/collect_jobs.py --config ~/.job-outreach/config.yaml
python scripts/send_digest.py --config ~/.job-outreach/config.yaml --dry-run
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode digest
```
