# 求职邮件 Skill 部署与运行指南（DEPLOY）

本文说明如何将 `job-application-email` 部署到本机或服务器，并在工作日 **09:30 / 14:30**（`Asia/Shanghai`）自动向目标公司发送求职邮件（固定自我介绍 + 简历 PDF）。

仓库：https://github.com/ShaoTiC/UserAPI1  
Skill 分支：`cursor/job-application-email-skill-1d7d`  
Skill 路径：`.cursor/skills/job-application-email/`

---

## 目录

1. [前置条件](#1-前置条件)
2. [获取代码](#2-获取代码)
3. [安装依赖](#3-安装依赖)
4. [开通发件邮箱 SMTP](#4-开通发件邮箱-smtp)
5. [创建本地私有配置](#5-创建本地私有配置)
6. [上线前四步验收](#6-上线前四步验收)
7. [定时任务部署](#7-定时任务部署)
8. [日常运维](#8-日常运维)
9. [在 Cursor 中作为 Skill 使用](#9-在-cursor-中作为-skill-使用)
10. [故障排查](#10-故障排查)
11. [完整 Checklist](#11-完整-checklist)

---

## 1. 前置条件

| 项目 | 要求 |
|------|------|
| 运行环境 | 长期开机的本机，或 Linux/macOS 云主机 |
| Python | 3.10+ |
| 发件邮箱 | 已开通 SMTP（QQ 使用「授权码」，不是登录密码） |
| 简历 | PDF，建议 ≤ 5MB |
| 公司列表 | 真实招聘邮箱（CSV） |
| 网络 | 能访问对应 SMTP（如 `smtp.qq.com:465`） |

相关文档：

- 流程与失败码：`SKILL.md`
- 审核标准：`references/review_standards.md`
- 测试用例：`tests/test_cases.md`

---

## 2. 获取代码

### 2.1 Git 克隆（推荐）

```bash
git clone https://github.com/ShaoTiC/UserAPI1.git
cd UserAPI1
git checkout cursor/job-application-email-skill-1d7d
```

Skill 根目录（后文简称 `$SKILL_ROOT`）：

```text
UserAPI1/.cursor/skills/job-application-email
```

### 2.2 IntelliJ IDEA

1. **File → New → Project from Version Control**
2. URL：`https://github.com/ShaoTiC/UserAPI1.git`
3. Clone 后右下角切换分支到 `cursor/job-application-email-skill-1d7d`

### 2.3 使用 zip 包

仓库根目录有 `job-application-email.zip`，解压到任意路径即可，不必放在本仓库内。

---

## 3. 安装依赖

```bash
cd UserAPI1/.cursor/skills/job-application-email   # 即 $SKILL_ROOT
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

冒烟自检（不发送真实邮件）：

```bash
python tests/run_smoke.py
# 期望：SMOKE PASS
```

---

## 4. 开通发件邮箱 SMTP

以 **QQ 邮箱**为例（与 `assets/config.example.yaml` 默认一致）：

1. 登录 https://mail.qq.com
2. **设置 → 账户 → POP3/IMAP/SMTP**
3. 开启 **SMTP**，按提示验证并生成 **授权码**
4. 妥善保存授权码（后续放入环境变量，不要提交到 Git）

其他常见邮箱：

| 邮箱 | smtp_host | 端口 | 说明 |
|------|-----------|------|------|
| QQ | smtp.qq.com | 465 SSL | 授权码 |
| 163 | smtp.163.com | 465 SSL | 授权码 |
| Gmail | smtp.gmail.com | 587 STARTTLS | 应用专用密码；需改 config 的 ssl/starttls |

---

## 5. 创建本地私有配置

所有真实凭证与公司列表放在用户目录，**不要提交到仓库**。

```bash
mkdir -p ~/.job-outreach/reports

# Windows：在用户目录下创建 .job-outreach 文件夹
# 例如 C:\Users\<用户名>\.job-outreach\
```

### 5.1 配置文件

```bash
cp assets/config.example.yaml ~/.job-outreach/config.yaml
```

编辑 `~/.job-outreach/config.yaml`，至少确认以下字段：

```yaml
mail:
  provider: smtp
  from_email: "你的QQ号@qq.com"
  smtp_host: "smtp.qq.com"
  smtp_port: 465
  smtp_ssl: true
  smtp_username: "你的QQ号@qq.com"
  max_retries: 3
  retry_base_delay_sec: 2
  min_interval_sec: 8
  max_attachment_mb: 5

email:
  from_name: "邵俊凯"
  subject: "求职-Java开发实习生-邵俊凯-东北农业大学"
  attachment_filename: "邵俊凯-Java开发实习生-简历.pdf"
  closing: "附件为个人简历，感谢您抽空查阅。期待有机会与贵司交流。"

paths:
  companies: "~/.job-outreach/companies.csv"
  resume: "~/.job-outreach/resume.pdf"
  self_intro: "assets/self_intro.txt"   # 相对 $SKILL_ROOT
  state: "~/.job-outreach/state.json"

schedule:
  timezone: "Asia/Shanghai"
  morning: "09:30"
  afternoon: "14:30"
  batch_size: 5          # 新手建议先改为 1~3

security:
  daily_send_limit: 20   # 新手建议先小一点
  blocked_domains:
    - example.com
    - mailinator.com

report:
  dir: "~/.job-outreach/reports"
```

> 自我介绍正文由 `assets/self_intro.txt` 提供，**禁止改写**。仅可调整 `email.closing`。

### 5.2 公司邮箱列表

```bash
cp assets/companies.example.csv ~/.job-outreach/companies.csv
```

CSV **必须保留表头**：

```csv
company_id,company_name,website,email,note
c001,某某科技,https://xxx.com,hr@xxx.com,校招
c002,某某网络,https://yyy.com,campus@yyy.com,Java
```

建议：

- `company_id` 唯一
- 上线前先只放 **1 个你自己能查收的测试邮箱**
- 验证通过后再追加真实公司

### 5.3 简历 PDF

```bash
cp "assets/resume/邵俊凯-Java开发实习生-简历.pdf" ~/.job-outreach/resume.pdf
# 或复制你的最新简历为上述路径
```

### 5.4 环境变量（授权码）

**macOS / Linux（当前终端）：**

```bash
export JOB_OUTREACH_SMTP_PASSWORD='你的QQ授权码'
export JOB_OUTREACH_CONFIG="$HOME/.job-outreach/config.yaml"
```

可写入 `~/.zshrc` / `~/.bashrc` 持久化（勿将含密钥的文件提交 Git）。

**Windows PowerShell（当前会话）：**

```powershell
$env:JOB_OUTREACH_SMTP_PASSWORD="你的QQ授权码"
$env:JOB_OUTREACH_CONFIG="$HOME\.job-outreach\config.yaml"
```

---

## 6. 上线前四步验收

先进入 `$SKILL_ROOT` 并激活 `.venv`。

### 步骤 A：安全检查（必须 PASS）

```bash
python scripts/check_security.py --config ~/.job-outreach/config.yaml
```

期望输出末尾为 `PASS`。常见失败：

| 错误码 | 处理 |
|--------|------|
| `AUTH_MISSING` | 设置 `JOB_OUTREACH_SMTP_PASSWORD` |
| `RESUME_MISSING` | 检查 `~/.job-outreach/resume.pdf` |
| `INTRO_MISMATCH` | 恢复 `assets/self_intro.txt` 固定原文 |
| `INVALID_EMAIL` | 修正 CSV 邮箱格式 |
| `COMPANIES_MISSING` | 创建/修正 `companies.csv` |
| `SECURITY_BLOCKED` | 域名在黑名单，或 batch 超过日上限 |

### 步骤 B：Dry-run（不真发）

```bash
python scripts/send_batch.py \
  --config ~/.job-outreach/config.yaml \
  --dry-run --limit 1 --force-schedule
```

期望：日志含 `DRY_RUN`，并在 `~/.job-outreach/reports/` 生成报告。

### 步骤 C：实发 1 封到自己的测试邮箱

将 CSV 第一行改为你可登录查收的邮箱，然后：

```bash
python scripts/send_batch.py \
  --config ~/.job-outreach/config.yaml \
  --limit 1 --force-schedule --slot manual
```

验收标准：

1. 终端出现 `OK ...`
2. 测试邮箱收到正确主题、固定自我介绍正文、PDF 附件
3. `~/.job-outreach/state.json` 中对应记录 `status` 为 `sent`

若出现 `AUTH_FAILED`：检查授权码、SMTP 是否开启、`from_email` 是否与账号一致。

### 步骤 D：幂等确认（不重复发送）

对同一收件人再执行一次（不加 `--force`），该记录应被跳过。

---

## 7. 定时任务部署

机器需在工作日 09:30 / 14:30 保持开机且网络可用。将下文 `/绝对路径/job-application-email` 替换为你的 `$SKILL_ROOT`。

### 7.1 cron（Linux / macOS，推荐）

```bash
crontab -e
```

示例（请改成绝对路径；更推荐把密钥放到独立 env 文件）：

```cron
SHELL=/bin/bash

# 工作日 09:30
30 9 * * 1-5 cd /绝对路径/job-application-email && . .venv/bin/activate && . $HOME/.job-outreach/env.sh && python scripts/send_batch.py --config $HOME/.job-outreach/config.yaml --slot morning >> $HOME/.job-outreach/cron.log 2>&1

# 工作日 14:30
30 14 * * 1-5 cd /绝对路径/job-application-email && . .venv/bin/activate && . $HOME/.job-outreach/env.sh && python scripts/send_batch.py --config $HOME/.job-outreach/config.yaml --slot afternoon >> $HOME/.job-outreach/cron.log 2>&1
```

创建 `~/.job-outreach/env.sh`：

```bash
export JOB_OUTREACH_SMTP_PASSWORD='你的QQ授权码'
export JOB_OUTREACH_CONFIG="$HOME/.job-outreach/config.yaml"
```

```bash
chmod 600 ~/.job-outreach/env.sh
```

确认系统时区：

```bash
date
# 或 Linux: timedatectl
```

应与 `schedule.timezone: Asia/Shanghai` 一致，或保证 cron 触发时刻对应北京时间。

### 7.2 前台调度器（本机常开）

```bash
cd /绝对路径/job-application-email
source .venv/bin/activate
source ~/.job-outreach/env.sh
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
```

关闭终端即停止。可用 `tmux` / `nohup` / systemd 保活。

仅检查一轮（便于测试）：

```bash
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml --once
```

### 7.3 Windows 任务计划程序

1. 创建 `%USERPROFILE%\.job-outreach\run_morning.bat`：

```bat
@echo off
cd /d C:\path\to\job-application-email
call .venv\Scripts\activate.bat
set JOB_OUTREACH_SMTP_PASSWORD=你的授权码
set JOB_OUTREACH_CONFIG=%USERPROFILE%\.job-outreach\config.yaml
python scripts\send_batch.py --config %JOB_OUTREACH_CONFIG% --slot morning >> %USERPROFILE%\.job-outreach\cron.log 2>&1
```

2. 再复制一份为 `run_afternoon.bat`，将 `--slot morning` 改为 `--slot afternoon`。
3. 打开「任务计划程序」→ 创建基本任务：
   - 触发器：每周一至五 9:30 / 14:30
   - 操作：启动对应 bat

---

## 8. 日常运维

### 8.1 发送前检查（可选）

```bash
python scripts/check_security.py --config ~/.job-outreach/config.yaml
```

### 8.2 查看结果

```bash
# 发送状态
cat ~/.job-outreach/state.json

# 报告目录
ls ~/.job-outreach/reports/
# 例如：report-2026-07-22-morning.md

# 定时日志
tail -n 100 ~/.job-outreach/cron.log
```

### 8.3 失败重试

```bash
python scripts/send_batch.py \
  --config ~/.job-outreach/config.yaml \
  --retry-failed --slot manual --force-schedule
```

### 8.4 扩充公司列表

向 `~/.job-outreach/companies.csv` 追加新行即可。已标记 `sent` 的记录默认不会重发（除非 `--force`）。

### 8.5 建议发送节奏

| 阶段 | batch_size | daily_send_limit |
|------|------------|------------------|
| 第 1–2 天 | 1–2 | 5 |
| 稳定后 | 3–5 | 15–30 |
| 谨慎上限 | ≤10 | ≤40 |

避免短时间大量投递触发反垃圾策略。

---

## 9. 在 Cursor 中作为 Skill 使用

1. 将整个 `job-application-email` 目录复制到：
   - 个人技能：`~/.cursor/skills/job-application-email/`
   - 或项目技能：`<项目>/.cursor/skills/job-application-email/`
2. 在对话中明确说明使用本 skill / 求职定时邮件流程。
3. Agent 会按 `SKILL.md` 执行：检查 → dry-run → 发送 → 写报告。

**真正的定点发送**仍建议依赖 cron / 任务计划程序，不要只依赖手动对话触发。

---

## 10. 故障排查

| 现象 | 处理 |
|------|------|
| `AUTH_FAILED` | 重做授权码；确认 SMTP 已开；From 与账号一致。会熔断整批，修好后再发 |
| `RATE_LIMITED` | 增大 `min_interval_sec`，减小 `batch_size`；下一时段 `--retry-failed` |
| `INVALID_RECIPIENT` | 回官网核对邮箱并更新 CSV；该条标记为 `invalid` |
| `NOT_WORKDAY` | 周末默认跳过；临时测试加 `--force-schedule` |
| 到点未发送 | 查看 `cron.log`；机器是否休眠；cron 中 venv/路径/环境变量是否生效 |
| 对方未收到 | 查发件箱与对方垃圾箱；降低频率；必要时换企业邮 |
| `SPAM_REJECTED` | 本 slot 停止，次日再试；勿改自我介绍灌水 |
| `STATE_CORRUPT` | 从 `state.json.bak` 恢复 |
| `ATTACHMENT_TOO_LARGE` | 压缩简历或提高 `max_attachment_mb`（仍建议 ≤5–10MB） |

失败码与重试策略详见 `SKILL.md` 中「失败场景、排查与重试」。

---

## 11. 完整 Checklist

```text
[ ] clone 仓库并 checkout skill 分支（或解压 zip）
[ ] 创建 venv 并 pip install -r requirements.txt
[ ] python tests/run_smoke.py → SMOKE PASS
[ ] 开通邮箱 SMTP，取得授权码
[ ] 写好 ~/.job-outreach/config.yaml
[ ] 写好 ~/.job-outreach/companies.csv（先测试邮箱）
[ ] 放置 ~/.job-outreach/resume.pdf
[ ] export JOB_OUTREACH_SMTP_PASSWORD（或 env.sh）
[ ] check_security.py → PASS
[ ] dry-run 1 封成功
[ ] 实发 1 封到自己邮箱并确认附件
[ ] 确认幂等（不重复发送）
[ ] 替换/追加真实公司列表（先少量）
[ ] 配置 cron 或 Windows 任务计划（09:30 / 14:30）
[ ] 次日检查 reports/、state.json、cron.log
```

---

## 附录：常用命令速查

```bash
# 安全检查
python scripts/check_security.py --config ~/.job-outreach/config.yaml

# 预览 1 封
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --dry-run --limit 1 --force-schedule

# 实发（受 batch_size / 日限额约束）
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --slot morning

# 只重试失败/延期
python scripts/send_batch.py --config ~/.job-outreach/config.yaml --retry-failed --force-schedule

# 前台调度
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
```
