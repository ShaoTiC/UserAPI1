# 电商 AI 客服订单进度追踪 Skill（Java）

模拟淘宝/京东风格的 AI 客服对话（用户追踪已购商品进度），并在多种场景下检测回复是否符合规范。

## 能力

- 12 个内置进度场景（待付款 → 签收/退款/异常等）
- 合规模拟客服回复生成
- 违规样例生成（用于检测器回归）
- 11 条可机检规范 + 结构化报告
- JUnit5 场景参数化测试 + CLI 演示

## 运行

```bash
cd ecommerce-cs-skill
./mvnw test
./mvnw -q -DskipTests package
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --list
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar S06_LOGISTICS_EXCEPTION
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --regression
```

## 代码入口

| 类 | 作用 |
|----|------|
| `EcommerceOrderTrackingSkill` | Skill 门面 |
| `CompliantCustomerServiceAgent` | 合规模拟回复 |
| `ComplianceChecker` | 规范检测 |
| `ScenarioCatalog` | 场景库 |
| `EcommerceCsSkillMain` | 命令行演示 |

## 设计假设（待你确认）

本实现按常见电商客服服务质量基线做了可机检近似；以下点若与你的真实规范不一致，请直接改规范表或反馈：

1. **「规范」来源未指定**：当前使用内置 11 条规则（隐私脱敏、状态准确、不编造、异常升级等），不是某一平台官方条文。
2. **客服回复来源**：默认用规则模板模拟合规/违规回复，便于确定性测试；未接真实大模型 API。
3. **平台差异**：淘宝/京东物流字段做了统一抽象（承运商+运单号+轨迹），未分别建模两套接口。
4. **身份核验**：仅校验「订单属于当前 userId」；未模拟短信验证码、人脸等强核身。
5. **交付形态**：Java 库 + CLI + Cursor `SKILL.md`；未做 Web UI / HTTP API（可按需加）。

## 目录

```text
ecommerce-cs-skill/
  src/main/java/com/ecommerce/cs/
    model/ scenario/ service/ compliance/ skill/
  src/test/java/...
.cursor/skills/ecommerce-order-tracking-cs/SKILL.md
```
