# 运行报告

- 日期：{{date}}
- 时段/模式：{{slot}}
- 时区：{{timezone}}
- Dry-run：{{dry_run}}
- 生成时间：{{generated_at}}

## 汇总

| 指标 | 数量 |
|------|------|
| 本批条目 | {{total_count}} |
| 成功 | {{success_count}} |
| 失败 | {{fail_count}} |
| 跳过/预览 | {{skip_count}} |

## 明细

| 公司 | 岗位/邮箱 | 链接或说明 | 结果 |
|------|-----------|------------|------|
{{result_rows}}

## 失败排查（Digest）

- [ ] 采集 `errors` 是否集中在某几家公司？
- [ ] 是否 JS 渲染导致 HTML 为空？考虑改 RSS/API
- [ ] 关键词是否过严导致 `NO_JOBS`？
- [ ] 是否 `AUTH_FAILED`？重做授权码
- [ ] 是否今日已发送？需要则 `--force`

## 失败排查（Outreach，若启用）

- [ ] `AUTH_FAILED` / `RATE_LIMITED` / `INVALID_RECIPIENT`
- [ ] 简历与自我介绍是否通过 `--mode outreach` 检查

## 次日行动

1. 更新无效的 `careers_url`
2. 确认定时任务仍在工作日 `digest_time` 触发
3. 对未成功发送的摘要直接重跑 `send_digest.py`
