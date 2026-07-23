# 测试用例（Digest 优先）

## TC-D01 fixture 采集与关键词过滤

**步骤**：使用 `assets/companies.example.csv` + fixture，运行 `collect_jobs.py`

**期望**：
- demo 公司返回匹配 Java/后端/实习/Agent/校招 的岗位
- 「前端视觉设计」「产品运营」等被过滤

## TC-D02 摘要条数截断

**步骤**：`send_digest.py --dry-run --limit 2`

**期望**：正文仅 2 条岗位

## TC-D03 Dry-run 不标记已发送

**步骤**：dry-run 后检查 `state.json` 的 `digest_daily`

**期望**：不写入当日已发送（或保持原样）

## TC-D04 去重

**步骤**：实发一次（或手动写入 `seen_jobs`）后再次 `collect_jobs`

**期望**：相同 `job_id` 进入 `known_jobs` 而非 `new_jobs`

## TC-D05 digest 安全检查不要求简历

**步骤**：`check_security.py --mode digest`（可不配置 resume）

**期望**：无 `RESUME_MISSING`；缺 `digest.to_email` 则 FAIL

## TC-D06 CSV schema

**步骤**：去掉 `careers_url` 列

**期望**：`COMPANIES_SCHEMA`

## TC-D07 html_regex 缺正则

**步骤**：`source_type=html_regex` 且 `item_regex` 为空

**期望**：`ITEM_REGEX_MISSING`

## TC-D08 同日不重复发送

**步骤**：写入 `digest_daily[今日]` 后再跑 `send_digest.py`

**期望**：`ALREADY_SENT`；加 `--force` 可再发

## TC-D09 非工作日跳过

**步骤**：周末运行 `run_daily.py`（不加 `--force-schedule`）

**期望**：`NOT_WORKDAY`

## TC-D10 邮件发送失败重试

**步骤**：错误授权码实发

**期望**：`AUTH_FAILED`，不写成功标记

## TC-O01～（outreach 兼容）

保留旧用例：自我介绍一致性、简历缺失、dry-run 外投等，运行时加 `--mode outreach`。详见历史 `test_cases` 思路与 `tests/run_smoke.py`。
