---
name: ecommerce-order-tracking-cs
description: 模拟电商平台（淘宝/京东风格）AI 客服订单进度追踪对话，并对回复做多场景规范检测。在用户提到订单物流、快递进度、客服话术质检、回复是否合规时使用。
---

# 电商 AI 客服 · 订单进度追踪与规范检测

用 Java Skill 完成两件事：

1. **模拟对话**：用户已下单，向 AI 客服询问商品/物流进度，按场景生成合规范回复。
2. **规范检测**：对模拟回复或外部待测回复，按可机检规则输出 PASS/FAIL 报告。

## 何时使用

- 用户要「查订单到哪了 / 什么时候发货 / 为什么还没到」
- 需要验证客服话术是否符合隐私、准确性、异常升级等规范
- 需要批量回归多种物流状态场景

## 项目位置

```text
ecommerce-cs-skill/          # Java 实现
.cursor/skills/ecommerce-order-tracking-cs/SKILL.md
```

## 快速运行

```bash
cd ecommerce-cs-skill
./mvnw -q test
./mvnw -q -DskipTests package
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --list
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar S01_IN_TRANSIT
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --regression
```

## 内置场景（12）

| ID | 场景 |
|----|------|
| S01_IN_TRANSIT | 运输中正常查询 |
| S02_PENDING_PAYMENT | 待付款 |
| S03_PENDING_SHIPMENT | 已付款待发货 |
| S04_OUT_FOR_DELIVERY | 派送中 |
| S05_DELIVERED | 已签收 |
| S06_LOGISTICS_EXCEPTION | 物流异常滞留 |
| S07_MISSING_ORDER_ID | 未提供订单号 |
| S08_ORDER_NOT_FOUND | 订单不存在 |
| S09_RETURNING | 退货中 |
| S10_REFUNDED | 已退款 |
| S11_CANCELLED | 已取消 |
| S12_DELAYED_SHIPMENT | 超时未发货 |

## 规范编码

| 编码 | 含义 |
|------|------|
| ORDER_ID_REQUIRED | 无订单号时先索取 |
| ORDER_NOT_FOUND_HANDLING | 查无订单正确处理 |
| STATUS_ACCURACY | 状态与事实一致 |
| TRACKING_COMPLETENESS | 承运商+运单号完整 |
| NO_FABRICATION | 不编造物流 |
| PRIVACY_MASKING | 手机/地址脱敏 |
| POLITENESS | 礼貌专业 |
| ACTIONABLE_NEXT_STEP | 可执行下一步 |
| EXCEPTION_HANDLING | 异常原因说明 |
| ESCALATION_PATH | 催办/转人工路径 |
| NO_OVERPROMISE | 不做过度承诺 |

## Agent 工作流

1. 确认用户场景（或选用内置场景 ID）。
2. 若要演示合规客服：调用 `EcommerceOrderTrackingSkill.simulateCompliantReply(scenarioId)`。
3. 若要质检某段回复：调用 `evaluate(scenarioId, replyText)`，展示 `ComplianceReport.render()`。
4. 回归时运行 `--regression` 或单元测试，确认合规模拟全过、违规样例能被检出。

## 规则

- **以订单事实为准**：不得编造轨迹、运单、到达时间。
- **先身份后详情**：缺订单号先问；查无则引导核对，不臆测。
- **隐私优先**：完整手机号、详细地址不得明文输出。
- **异常可升级**：滞留/超时必须给催办或转人工路径。
- **检测可解释**：每条规范输出 PASS/FAIL 与原因，便于话术整改。
