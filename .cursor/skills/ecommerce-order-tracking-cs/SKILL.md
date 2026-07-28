---
name: ecommerce-order-tracking-cs
description: 模拟电商平台（淘宝/京东风格）AI 客服订单进度追踪对话；可调用 OpenAI 兼容内部大模型生成回复并做多场景规范质检。在用户提到订单物流、快递进度、客服话术质检、回复是否合规、LLM 客服时使用。
---

# 电商 AI 客服 · 订单进度追踪与规范检测

用 Java Skill 完成：

1. **真实 LLM 对话**：对接内部大模型（OpenAI `/v1/chat/completions` 兼容）生成客服回复
2. **规范质检**：对 LLM / 模板 / 外部回复做 11 条可机检规范检测
3. **场景模拟部署**：Web 演示台 / CLI / Docker

## 何时使用

- 用户要「查订单到哪了 / 什么时候发货 / 为什么还没到」
- 需要验证客服话术是否符合隐私、准确性、异常升级等规范
- 需要把内部大模型接到客服流程并做质检回归

## 项目位置

```text
ecommerce-cs-skill/
.cursor/skills/ecommerce-order-tracking-cs/SKILL.md
```

## 接入内部大模型并运行

详见 [ecommerce-cs-skill/DEPLOY.md](../../../ecommerce-cs-skill/DEPLOY.md)。

```bash
cd ecommerce-cs-skill
cp .env.example .env   # 配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
./mvnw -q -DskipTests package

# 演示（无 GPU 可用 mock）
python3 deploy/mock_internal_llm.py --port 18080 &
export LLM_BASE_URL=http://127.0.0.1:18080/v1 LLM_API_KEY=local LLM_MODEL=mock-internal-qwen
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --serve 8080
# 打开 http://127.0.0.1:8080/ → 选择场景 →「调用真实 LLM 并质检」
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

## Agent 工作流

1. 确认 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 已指向内部大模型（或 mock）。
2. 选场景后调用 `EcommerceOrderTrackingSkill.withLlmFromEnv().simulateWithLlmAndInspect(id)`。
3. 展示 `LlmInspectionResult.render()`（回复 + PASS/FAIL）。
4. 演示部署优先启动 `--serve`，按 [DEPLOY.md](../../../ecommerce-cs-skill/DEPLOY.md) 操作。

## 规则

- **以订单事实为准**：prompt 注入订单快照，禁止编造轨迹。
- **先身份后详情**：缺订单号先问；查无则引导核对。
- **隐私优先**：完整手机号、详细地址不得明文输出。
- **异常可升级**：滞留/超时必须给催办或转人工路径。
- **LLM 失败如实告知**：连接失败时提示检查网关配置，不假装已回复。
