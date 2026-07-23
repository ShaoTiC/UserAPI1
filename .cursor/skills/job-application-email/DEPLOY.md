# 部署指南：官网新岗位即时速递

## IDEA 打开本仓库（可直接粘贴）

**File → New → Project from Version Control**，URL：

```text
https://github.com/ShaoTiC/UserAPI1.git
```

克隆后切换分支：

```text
cursor/job-application-email-skill-1d7d
```

**Directory（本地目录）怎么填：**

IDEA 会要求选择 Directory，填你希望存放仓库的本地路径即可，例如：

```text
C:\Users\你的用户名\IdeaProjects\UserAPI1
```

或 macOS：`/Users/你的用户名/IdeaProjects/UserAPI1`  

选一个空目录/新文件夹名；clone 完成后 skill 在：

```text
<你的 Directory>/.cursor/skills/job-application-email/
```

异常与特殊情况处理见：[docs/EXCEPTION_HANDLING.md](docs/EXCEPTION_HANDLING.md)

Skill 目录：`.cursor/skills/job-application-email/`

---

## 当前规则（已按你的确认落地）

1. 公司：腾讯 / 字节 / 阿里 / 百度 / 美团 / OPPO / 米哈游 / 小红书 / 拼多多  
2. **无固定发送时间**：轮询发现新岗位后立刻推送  
3. 关键词：Java / 后端 / 实习 / 校招 / Agent / 开发  
4. **只发全新，宁少勿多**（不凑满 10 条）  
5. 邮件含官网链接 + 职位链接 + 职位内容  
6. **关闭外投简历**

说明：官网不会主动 webhook，本 skill 用短间隔轮询近似「立刻」（默认 600 秒，可改更短）。

---

## 安装

```bash
cd UserAPI1/.cursor/skills/job-application-email
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

QQ SMTP：开启授权码后

```bash
export JOB_OUTREACH_SMTP_PASSWORD='你的授权码'
mkdir -p ~/.job-outreach/cache ~/.job-outreach/reports
cp assets/config.example.yaml ~/.job-outreach/config.yaml
cp assets/companies.example.csv ~/.job-outreach/companies.csv
```

确认 `digest.to_email: 3461630168@qq.com`。

---

## 运行

```bash
# 检查
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode digest

# 第一轮：建立基线（通常不发邮件）
python scripts/run_daily.py --config ~/.job-outreach/config.yaml

# 之后：有新岗位才会发到邮箱
python scripts/run_daily.py --config ~/.job-outreach/config.yaml

# 持续监控（推荐长期运行 / tmux / 系统服务）
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
# 或更勤快： --poll-sec 300
```

Windows 可用任务计划程序每 N 分钟执行一次 `run_daily.py`，效果等同轮询。

---

## 验收

1. 首次运行日志含 `BASELINE: seeded ... without notify`  
2. dry-run：`python scripts/run_daily.py --config ... --dry-run`  
3. 人为清空某条 `seen_jobs` 或等待官网更新后，应收到「新岗位速递」  
4. 邮件中可见官网 + 职位链接 + 内容摘要  

---

## 排障

| 问题 | 处理 |
|------|------|
| 某公司 0 岗位 | 加大 `playwright_wait_ms`；核对 `careers_url` |
| Chromium 缺失 | `playwright install chromium` |
| 不推送 | 看是否仍在基线后无增量（`NO_NEW_JOBS` 正常） |
| 发信失败 | 检查授权码与 SMTP |

更完整说明见 `SKILL.md`。
