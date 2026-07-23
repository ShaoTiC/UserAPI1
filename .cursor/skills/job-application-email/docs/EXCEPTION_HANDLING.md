# 异常与特殊情况处理手册

本文整理本 skill（官网新岗位即时速递）运行中可能遇到的异常、边界情况，以及推荐处理方案。  
适用路径：`.cursor/skills/job-application-email/`

---

## 0. IDEA 的 Directory 怎么填

在 **File → New → Project from Version Control** 中：

| 字段 | 填什么 |
|------|--------|
| URL | `https://github.com/ShaoTiC/UserAPI1.git` |
| Directory | 本地要存放仓库的**空文件夹路径**（IDEA 会把仓库 clone 到这里） |

示例（按你电脑改用户名即可）：

```text
# Windows
C:\Users\你的用户名\IdeaProjects\UserAPI1

# macOS
/Users/你的用户名/IdeaProjects/UserAPI1

# Linux
/home/你的用户名/IdeaProjects/UserAPI1
```

说明：

1. Directory 一般选一个**尚不存在或为空**的目录；不要选已有乱七八糟文件的文件夹。  
2. Clone 完成后，项目根是 `UserAPI1/`；**skill 代码**在：

```text
UserAPI1/.cursor/skills/job-application-email/
```

3. 切换分支：右下角 Git 分支 → `cursor/job-application-email-skill-1d7d`  
4. 运行脚本时，终端工作目录应是上述 skill 目录（或在配置里用绝对路径）。

---

## 1. 总览：异常分类

| 类别 | 典型现象 | 是否阻断整轮 |
|------|----------|--------------|
| A. 环境/依赖 | Chromium 缺失、PyYAML 未装 | 是 |
| B. 配置/凭证 | 授权码错误、缺 to_email | 是（发信前） |
| C. 单公司采集失败 | 某站超时、反爬、0 岗位 | 否（跳过该公司） |
| D. 增量逻辑 | 首次基线、无新岗位 | 否（正常） |
| E. 邮件发送 | SMTP 失败、进垃圾箱 | 视错误类型 |
| F. 状态文件 | state 损坏、磁盘满 | 可能阻断 |
| G. 调度/进程 | 休眠、进程被杀、重复启动 | 漏推或重复轮询 |
| H. 内容质量 | 误报导航链、漏报新岗 | 体验问题 |

设计原则：**单公司失败不拖垮全局**；**只推全新岗位**；发信失败**不标记已通知**，以便下轮重试。

---

## 2. 环境与依赖（A）

### A1. `ModuleNotFoundError: playwright` / `pyyaml`

**现象**：脚本启动即崩。  
**处理**：

```bash
cd .cursor/skills/job-application-email
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### A2. Playwright 找不到浏览器

**现象**：`Executable doesn't exist` / browser launch failed。  
**处理**：

```bash
playwright install chromium
# Linux 若缺系统库，按官方提示安装依赖，例如：
# playwright install-deps chromium
```

### A3. Python 版本过低

**现象**：语法/类型相关报错。  
**处理**：使用 Python **3.10+**。

### A4. IDEA 终端未激活 venv

**现象**：能跑系统 Python，却缺包。  
**处理**：在 IDEA Terminal 先 `source .venv/bin/activate`（Windows 用 `.\.venv\Scripts\Activate.ps1`），或把 IDEA 的 Project Interpreter 指到该 venv。

---

## 3. 配置与凭证（B）

### B1. `AUTH_MISSING` / `AUTH_FAILED`

**现象**：安全检查失败或发信 535。  
**原因**：未设 `JOB_OUTREACH_SMTP_PASSWORD`，或授权码过期/错误；From 与账号不一致。  
**处理**：

1. QQ 邮箱重新生成授权码（不是登录密码）  
2. `export JOB_OUTREACH_SMTP_PASSWORD='...'`  
3. 确认 `mail.from_email` / `smtp_username` 均为 `3461630168@qq.com`  
4. **认证失败会停止本轮发信**（避免刷爆）；修好后再跑

### B2. `CONFIG_INVALID: digest.to_email`

**处理**：在 `~/.job-outreach/config.yaml` 设置：

```yaml
digest:
  to_email: "3461630168@qq.com"
```

### B3. `COMPANIES_MISSING` / `COMPANIES_SCHEMA`

**现象**：CSV 路径错或缺列。  
**处理**：确认 `paths.companies` 指向有效文件；digest 模式必填列：

`company_id,company_name,careers_url,source_type`

### B4. 配置写进了明文密码并提交 Git

**风险**：密钥泄露。  
**处理**：立刻作废授权码；改用环境变量；从 Git 历史清理（若已推送需轮换密钥）。

---

## 4. 采集阶段（C）

### C1. 单公司 `WARN xxx: TimeoutError` / `URLError`

**现象**：日志对该公司报错，其它公司继续。  
**处理**：

1. 加大 `crawl.timeout_sec`、`playwright_wait_ms`  
2. 检查本机网络/代理能否打开该官网  
3. 下轮自动再试；无需人工清状态

### C2. 某站长期 0 条匹配岗位

**可能原因**：

- 页面是强登录/验证码  
- `careers_url` 不是职位列表页  
- 关键词过严（标题不含 Java/后端等）  
- 前端改版，链接结构变化  

**处理**：

1. 浏览器人工打开 `careers_url`，确认列表是否可见  
2. 换成更接近「职位列表」的 URL（见 `companies.example.csv`）  
3. 临时对该公司放宽 `keywords` 列（`|` 分隔）做对比  
4. 增大 `playwright_wait_ms`（如 10000～15000）  
5. 仍不行：在 CSV `note` 标注「需人工」，或临时改 `source_type`（若后续有官方 JSON）

### C3. 反爬 / 人机验证 / IP 封禁

**现象**：页面只有验证码，或采集到无关壳页面。  
**处理**：

1. 把 `schedule.poll_interval_sec` 调大（如 900～1800），降低频率  
2. 避免多进程同时打同一站点  
3. 必要时换网络环境；不要用代理池乱撞（易违反网站条款）  
4. 接受「该站暂时人工看」——skill 对其它站仍可用

### C4. Playwright 点击「职位」点错或弹窗遮挡

**现象**：采到导航文案、登录页。  
**处理**：代码已有导航词黑名单；若仍误采，在状态里会变成 seen。可：

1. 调整该公司 `careers_url` 直达列表页  
2. 手动从 `state.json` 的 `seen_jobs` 删除误报 id（谨慎）  
3. 反馈具体页面结构以便加站点适配

### C5. 九家中部分成功、部分失败

**设计**：正常。报告/缓存的 `errors` 会列出失败公司。  
**处理**：看 `~/.job-outreach/cache/jobs-YYYY-MM-DD.json` 的 `errors` 字段，逐个修 URL/等待时间。

---

## 5. 增量与推送逻辑（D）

### D1. 首次运行不发邮件（`BASELINE: seeded ...`）

**原因**：`baseline_on_first_run: true`，避免把官网存量岗位一次推爆邮箱。  
**处理**：属预期。第二轮开始只推「相对基线的新增」。  
若你想**第一次就推当前全部匹配岗**：

```yaml
crawl:
  baseline_on_first_run: false
```

（不推荐，邮件可能很多。）

### D2. `NO_NEW_JOBS`

**原因**：本轮相对 `seen_jobs` 没有新岗位。  
**处理**：正常。不是故障。官网没更新时不应强行发信。

### D3. 漏推（官网明明有新岗，邮件没有）

**可能原因**：

1. 轮询间隔内尚未跑到（默认 600s）  
2. 标题不含关键词  
3. 岗位被采到但 `job_id` 与旧帖相同（标题+链接未变）  
4. 进程没在跑 / 电脑休眠  
5. 首次基线时已被 seed  

**处理**：

1. 缩短 `poll_interval_sec`（如 300）  
2. 确认 `schedule_runner` 持续运行  
3. 查 cache 里是否出现在 `new_jobs`  
4. 关闭休眠或放到云主机  
5. 核对关键词与职位标题

### D4. 重复推送同一岗位

**设计**：成功发送后写入 `seen_jobs`，不应再推。  
**若仍重复**：

1. 是否发信成功但写 state 失败（磁盘权限）  
2. 是否删过/换过 `state.json`  
3. 同一岗位换了 URL → `job_id` 变了，会视为新岗（可接受；或后续做「标题相似度」去重）

### D5. 一次更新岗位特别多

**处理**：`digest.max_per_push`（默认 30）截断单封邮件大小；**剩余新岗仍留在 cache 的 new 逻辑里**——注意：当前实现是「本轮选中并成功发送的才写入 seen」。若截断导致未进邮件的 new 岗：

- **现状风险**：未选中的 new 若未写入 seen，下轮还会再尝试推送（合理）  
- 若希望「截断部分也标已见」：需改代码策略（可后续加 `mark_unsent_as_seen: false` 开关）

**建议**：保持「未发出去的仍算新」，避免丢提醒。

### D6. 同一天多封邮件

**原因**：无「每日一封」限制；有更新就推。  
**处理**：属预期。若嫌多，加大轮询间隔，或提高关键词精度。

---

## 6. 邮件发送（E）

### E1. `TIMEOUT` / 网络闪断

**处理**：`lib_mail` 指数退避最多 3 次。仍失败则本轮不写 `notified_at`，下轮可重试。

### E2. `RATE_LIMITED`（发送频率限制）

**处理**：增大轮询间隔；QQ 日发送有上限时改小推送频率或次日再试。

### E3. 邮件进垃圾箱

**处理**：

1. 在 QQ 邮箱把发件人设为受信  
2. 检查主题是否过于营销（当前主题较中性）  
3. 自己发给自己有时仍进垃圾箱，手动移回并「这不是垃圾邮件」

### E4. 收到空内容 / 乱码

**处理**：确认 SMTP 使用 UTF-8（当前 `EmailMessage` 文本模式）；若 HTML 被剥离，看纯文本部分是否完整。

### E5. Dry-run 误以为已发送

**现象**：`--dry-run` 只打印预览，不改「已通知」成功路径（不写 notified）。  
**处理**：验收时看日志是否含 `DRY_RUN`；实发需去掉 `--dry-run`。

---

## 7. 状态与磁盘（F）

### F1. `STATE_CORRUPT`

**处理**：

```bash
cp ~/.job-outreach/state.json.bak ~/.job-outreach/state.json
# 若无备份：移走坏文件，下一轮会重建（会重新基线/可能再推一批，注意）
```

### F2. 磁盘满 / 无写权限

**现象**：报告或 state 写失败。  
**处理**：清理 `~/.job-outreach/cache`、`reports`；检查目录权限。

### F3. 多台机器同时跑同一 skill

**风险**：两份 `state.json` 不一致 → 重复推送或漏推。  
**处理**：**只在一台机器**跑 `schedule_runner`；state 放该机本地。

### F4. 换电脑迁移

**处理**：拷贝 `~/.job-outreach/config.yaml`、`companies.csv`、`state.json`；重新设环境变量与 venv/playwright。

---

## 8. 调度与进程（G）

### G1. 电脑休眠 / 合盖

**现象**：轮询暂停，不能「立刻」感知更新。  
**处理**：云主机 / 家用 NAS / 关闭休眠；或 cron 每 N 分钟唤醒执行 `run_daily.py`。

### G2. 终端关闭导致 watcher 退出

**处理**：

```bash
# tmux 示例
tmux new -s jobwatch
python scripts/schedule_runner.py --config ~/.job-outreach/config.yaml
# Ctrl+B D 脱离
```

或配置 systemd / Windows 任务计划。

### G3. 同时开两个 `schedule_runner`

**风险**：重复采集、重复发信竞态。  
**处理**：只保留一个进程；用 `pgrep -af schedule_runner` 检查。

### G4. 时钟/时区错误

**影响**：报告时间戳不准；轮询本身不依赖「整点」。  
**处理**：系统时区设为 `Asia/Shanghai`，与 config 一致。

---

## 9. 内容质量与合规（H）

### H1. 推送了非技术岗（误报）

**原因**：标题碰巧含「开发」「校招」等。  
**处理**：收紧该公司 `keywords`；或在黑名单逻辑中排除（可后续加 `title_exclude`）。

### H2. 漏了心仪岗位

**原因**：标题不含默认关键词（如只写「软件工程师」）。  
**处理**：对该公司 CSV `keywords` 增加词，例如 `工程师|后端|Java`。

### H3. 职位内容只有一行标题

**原因**：列表页锚文本短，详情需二次打开。  
**处理**：当前以列表摘要为准；后续可加「详情页二次抓取」（成本更高、更易反爬）。

### H4. 网站服务条款 / 爬虫道德与法律风险

**说明**：自动化访问招聘站可能触发网站限制。  
**处理**：控制频率、仅用于个人求职信息聚合、勿传播破解验证码方案；若官网提供官方订阅/RSS/邮件提醒，优先改用官方渠道。

---

## 10. 推荐处置流程（运维 Checklist）

当「没收到邮件」时按序查：

```text
1. schedule_runner / run_daily 进程是否在跑？
2. cron.log 或终端是否有 AUTH_FAILED / 全员 WARN？
3. cache/jobs-*.json 的 new_count 是否为 0？（0 则属正常）
4. state.json 是否存在且可写？
5. QQ 邮箱垃圾箱是否有「新岗位速递」？
6. 单公司 careers_url 浏览器能否打开职位列表？
```

当「某公司一直失败」时：

```text
1. 记下 errors 原文
2. 加大 playwright_wait_ms 再试 --once
3. 更换更直的职位列表 URL
4. 仍失败 → 标记人工关注，不影响其它八家
```

---

## 11. 配置项速查（与异常相关）

| 配置 | 默认倾向 | 异常时怎么调 |
|------|----------|--------------|
| `schedule.poll_interval_sec` | 600 | 漏推→减小；反爬→增大 |
| `crawl.playwright_wait_ms` | 6000 | 0 条→增大到 10000+ |
| `crawl.timeout_sec` | 60 | 超时→增大 |
| `crawl.baseline_on_first_run` | true | 想首轮全推→false |
| `digest.max_per_push` | 30 | 单次更新极多时防邮件过大 |
| `digest.keywords` | 六词 | 误报→收紧；漏报→放宽 |

---

## 12. 已知局限（需预期）

1. **不是真正的官网推送**，是轮询，最短感知延迟 ≈ 一轮间隔。  
2. **强 JS / 登录墙站点**可能长期采不全（九家里个别站更脆）。  
3. **去重键**为公司+标题+URL，改链同岗可能再推一次。  
4. **外投简历已关闭**，本手册不覆盖投递失败类问题。  
5. 站点改版后选择器/链接结构变化需要改 `careers_url` 或加适配器。

---

## 13. 相关文件

| 文件 | 用途 |
|------|------|
| `DEPLOY.md` | 安装与 IDEA 打开方式 |
| `SKILL.md` | 功能与 Agent 流程 |
| `~/.job-outreach/state.json` | 已见岗位与推送日志 |
| `~/.job-outreach/cache/` | 每轮采集结果 |
| `~/.job-outreach/reports/` | 发送报告 |

若出现本文未覆盖的报错，请保留完整终端日志与对应 `jobs-*.json` 的 `errors` 字段，便于追加站点级适配。
