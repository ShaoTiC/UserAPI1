# 电商 AI 客服订单进度追踪 Skill（Java）

模拟淘宝/京东风格的 AI 客服对话（用户追踪已购商品进度），支持：

1. **真实 LLM（OpenAI 兼容内部大模型）生成回复**
2. **自动规范质检**
3. **Web / CLI / Docker 部署演示**

## 快速开始（接入内部大模型）

```bash
cd ecommerce-cs-skill
cp .env.example .env
# 编辑 .env：LLM_BASE_URL / LLM_API_KEY / LLM_MODEL

./mvnw -q test
./mvnw -q -DskipTests package

# 无 GPU 时可用 mock 网关验证整条链路
python3 deploy/mock_internal_llm.py --port 18080 &
export LLM_BASE_URL=http://127.0.0.1:18080/v1 LLM_API_KEY=local LLM_MODEL=mock-internal-qwen

java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --serve 8080
# 浏览器打开 http://127.0.0.1:8080/
```

完整部署说明见 **[DEPLOY.md](DEPLOY.md)**。

## 常用命令

| 命令 | 作用 |
|------|------|
| `--serve 8080` | Web 对话场景模拟 + 质检台 |
| `--llm S01_IN_TRANSIT` | 单场景真实 LLM + 质检 |
| `--llm-regression` | 12 场景全量 LLM 质检 |
| `--regression` | 规则模板回归（无需 LLM） |
| `--list` | 列出场景 |

## 代码入口

| 类 | 作用 |
|----|------|
| `OpenAiCompatibleLlmClient` | 内部大模型客户端 |
| `LlmQualityInspectionService` | LLM 回复 → 质检流水线 |
| `DialogueDemoServer` | HTTP 演示服务 |
| `ComplianceChecker` | 11 条规范检测 |
| `EcommerceCsSkillMain` | CLI 入口 |

## 目录

```text
ecommerce-cs-skill/
  src/main/java/com/ecommerce/cs/
    llm/ compliance/ model/ scenario/ service/ skill/ web/
  src/main/resources/web/index.html
  deploy/Dockerfile
  deploy/docker-compose.yml
  deploy/mock_internal_llm.py
  DEPLOY.md
  .env.example
```
