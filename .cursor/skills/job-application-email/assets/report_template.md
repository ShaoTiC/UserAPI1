# 求职投递报告

- 日期：{{date}}
- 时段：{{slot}}
- 时区：{{timezone}}
- Dry-run：{{dry_run}}
- 生成时间：{{generated_at}}

## 汇总

| 指标 | 数量 |
|------|------|
| 本批目标 | {{total_count}} |
| 成功 | {{success_count}} |
| 失败 | {{fail_count}} |
| 跳过/预览 | {{skip_count}} |

## 明细

| 公司 | 邮箱 | 结果码 | 尝试次数 | 说明 |
|------|------|--------|----------|------|
{{result_rows}}

## 失败排查（勾选）

- [ ] 是否出现 `AUTH_FAILED`？若是：停止批次，轮换授权码/API Key 后重试
- [ ] 是否出现 `RATE_LIMITED`？若是：增大间隔、减小 batch，下一 slot 用 `--retry-failed`
- [ ] 是否出现 `INVALID_RECIPIENT`？若是：回官网核对邮箱并更新 CSV
- [ ] 是否出现 `SPAM_REJECTED`？若是：降低频率 / 换企业邮，次日再发
- [ ] 是否触及 `daily_send_limit`？若是：等待次日

## 次日行动

1. 对 `failed` / `deferred` 执行：`python scripts/send_batch.py --config <cfg> --retry-failed`
2. 更新公司列表中的无效邮箱
3. 确认 cron / `schedule_runner.py` 仍在工作日 09:30 与 14:30 触发
