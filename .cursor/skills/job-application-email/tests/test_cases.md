# 求职邮件 Skill 测试用例

运行环境：Python 3.10+，已安装 `pyyaml`。以下路径以 skill 根目录为基准。

## TC-01 自我介绍一致性（阻断）

**步骤**
1. 备份 `assets/self_intro.txt`
2. 故意改动一个标点或字
3. 运行 `python scripts/check_security.py --config <cfg> --resume <pdf> --companies <csv>`

**期望**：exit ≠ 0，输出含 `INTRO_MISMATCH`

**恢复**：还原固定原文

---

## TC-02 简历缺失（阻断）

**步骤**：config 中 `paths.resume` 指向不存在文件，运行 `check_security.py`

**期望**：`RESUME_MISSING`，exit ≠ 0

---

## TC-03 非法邮箱（阻断）

**步骤**：CSV 中写入 `hr@` 或空邮箱，运行检查

**期望**：`INVALID_EMAIL`，且无有效收件人时 `NO_VALID_RECIPIENTS`

---

## TC-04 域名黑名单（阻断）

**步骤**：收件人为 `a@mailinator.com`

**期望**：`SECURITY_BLOCKED`

---

## TC-05 Dry-run 不实发

**步骤**

```bash
python scripts/send_batch.py --config <cfg> --dry-run --limit 1 --force-schedule --skip-security
```

**期望**
- 输出 `DRY_RUN`
- `state.json` 中对应记录状态不变为 `sent`
- 生成报告 `dry_run: True`

---

## TC-06 固定正文组装

**步骤**：dry-run 后检查日志/调试打印的 body（可临时在代码中 print，或对 `build_body` 做单元断言）

**期望**：正文以固定自我介绍开头；若配置了 `closing`，则以空行分隔追加

---

## TC-07 非工作日跳过

**步骤**：在模拟周六时间或等待周末，运行

```bash
python scripts/send_batch.py --config <cfg> --slot morning
```

**期望**：输出 `NOT_WORKDAY`，exit 0，无发送

**对照**：加 `--force-schedule` 后应进入选址逻辑

---

## TC-08 幂等不重发

**步骤**
1. 将某 `company_id|email` 在 state 标为 `sent`
2. 运行 `send_batch.py --limit 5`（不加 `--force`）

**期望**：该条不被选中

---

## TC-09 AUTH_FAILED 熔断

**步骤**：使用错误 SMTP 密码实发（或 mock），批次 limit≥2

**期望**
- 首封（或失败封）记 `AUTH_FAILED`
- 后续目标被跳过，日志含 `circuit open`

---

## TC-10 RATE_LIMITED 退避与 deferred

**步骤**：mock `send_smtp` 抛出含频率限制的错误，或临时把 `max_retries` 设为 2、`retry_base_delay_sec` 设为 0.1

**期望**
- 发生多次 attempt
- 最终状态 `deferred`（而非 `invalid`）
- 可用 `--retry-failed` 再次拾取

---

## TC-11 日上限

**步骤**：将 `security.daily_send_limit` 设为 1，state 中今日计数已为 1

**期望**：`SECURITY_BLOCKED: daily_send_limit reached`，exit 2

---

## TC-12 调度窗口

**步骤**

```bash
python scripts/schedule_runner.py --config <cfg> --once --window-sec 90
```

在非 09:30/14:30 窗口运行

**期望**：不触发 `send_batch`；在窗口内（可临时改 config 的 morning 为当前时间+1 分钟）应触发一次且同日同 slot 不重复（`fired` 去重）

---

## TC-13 报告模板渲染

**步骤**：任意 dry-run 后打开 `report.dir` 下 md

**期望**：`{{date}}` 等占位符均被替换；明细表有行或 `(empty)` 提示

---

## TC-14 附件大小超限

**步骤**：将 `max_attachment_mb` 设为 0.0001 后跑 `check_security.py`

**期望**：`ATTACHMENT_TOO_LARGE`

---

## TC-15 CSV schema

**步骤**：去掉 `company_id` 列

**期望**：`COMPANIES_SCHEMA`

---

## 自动化建议

可将 TC-01/02/03/04/05/07/08/11/14/15 做成无网络 CI；TC-09/10 用 mock；TC-06/12/13 做集成测试。真实 SMTP 联通性测试仅在本地手动执行。
