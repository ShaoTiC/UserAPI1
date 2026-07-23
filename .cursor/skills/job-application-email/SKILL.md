---
name: job-application-email
description: 持续轮询目标公司校招官网，发现匹配关键词的全新岗位后立即推送到用户邮箱（3461630168@qq.com）。推送含官网链接与职位内容；只发全新、宁少勿多。当用户提到招聘速递、官网新岗位监控、即时推送时使用本 skill。
disable-model-invocation: true
---

# Job Application Email（官网新岗位即时速递）

## 功能（当前）

1. 监控已配置的 **九家公司** 校招官网  
2. 关键词：`Java / 后端 / 实习 / 校招 / Agent / 开发`  
3. **无固定发送时间**：轮询发现全新岗位后**立刻**发邮件到 `3461630168@qq.com`  
4. **只发全新，宁少勿多**（不补齐、不要求每天 10 条）  
5. 邮件内容含：**公司官网链接** + **职位链接** + **职位内容摘要**  
6. **外投简历已关闭**

## 九家公司

| 公司 | 官网 | 采集页（careers_url） |
|------|------|----------------------|
| 腾讯 | https://join.qq.com/ | https://join.qq.com/post.html |
| 字节跳动 | https://jobs.bytedance.com/ | https://jobs.bytedance.com/campus/position |
| 阿里 | https://campus-talent.alibaba.com/campus/index | 同左 |
| 百度 | https://talent.baidu.com/jobs/ | 同左 |
| 美团 | https://zhaopin.meituan.com/web/campus | 同左 |
| OPPO | https://careers.oppo.com/university/oppo/campus | 同左 |
| 米哈游 | https://jobs.mihoyo.com/ | 同左 |
| 小红书 | https://job.xiaohongshu.com/campus | https://job.xiaohongshu.com/campus/position |
| 拼多多 | https://careers.pddglobalhr.com/campus/ | 同左 |

完整 CSV：`assets/companies.example.csv`（`source_type=playwright`）。

## 部署

详见 [DEPLOY.md](DEPLOY.md)。  
异常与特殊情况（含 IDEA Directory 说明）：[docs/EXCEPTION_HANDLING.md](docs/EXCEPTION_HANDLING.md)。

IDEA「从版本控制新建」：

- **URL**：`https://github.com/ShaoTiC/UserAPI1.git`
- **Directory**：本地空目录，如 `C:\Users\你\IdeaProjects\UserAPI1`（clone 后 skill 在该目录下 `.cursor/skills/job-application-email/`）

## 快速开始

```bash
cd .cursor/skills/job-application-email
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp assets/config.example.yaml ~/.job-outreach/config.yaml
cp assets/companies.example.csv ~/.job-outreach/companies.csv
export JOB_OUTREACH_SMTP_PASSWORD='QQ授权码'

# 安全检查
python scripts/check_security.py --config ~/.job-outreach/config.yaml --mode digest

# 单轮：采集；首次会建基线不推送；之后有新岗位才发信
python scripts/run_daily.py --config ~/.job-outreach/config.yaml

# 持续轮询（默认每 600 秒），有更新立刻推送
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
```

## Agent 清单

```text
Task Progress:
- [ ] 安装 playwright chromium
- [ ] 配置 SMTP 与 digest.to_email=3461630168@qq.com
- [ ] 使用九家公司 CSV
- [ ] 首次 run_daily 建立基线
- [ ] 二次 dry-run / 实跑验证只推送增量
- [ ] 启动 schedule_runner 持续监控
```

## 行为说明

| 项 | 行为 |
|----|------|
| 触发 | 轮询间隔内发现 `new_jobs` 立刻发送 |
| 首次运行 | `baseline_on_first_run: true` 把当前岗位记入 seen，不刷屏 |
| 补齐 | **不做**；没有新岗位则 `NO_NEW_JOBS` |
| 单次上限 | `max_per_push` 仅防邮件过大（默认 30） |
| 外投 | 关闭（`send_batch.py` 仅遗留，不调度） |

## 失败与排查

| 现象 | 处理 |
|------|------|
| playwright 报错 | `pip install playwright && playwright install chromium` |
| 某站采集 0 条 | 页面结构变化；调整 `careers_url` 或等待加载 `playwright_wait_ms` |
| `AUTH_FAILED` | 重做 QQ 授权码 |
| `NO_NEW_JOBS` | 正常（本轮无增量） |
| 反爬/验证码 | 加大 `poll_interval_sec`；人工打开官网确认 |

邮件发送仍使用 `lib_mail` 指数退避重试（最多 3 次）。

## 目录

```text
scripts/
  check_security.py / job_sources.py / collect_jobs.py
  send_digest.py / run_daily.py / schedule_runner.py
  lib_mail.py
  send_batch.py          # 已停用外投，保留文件不调度
assets/companies.example.csv
```
