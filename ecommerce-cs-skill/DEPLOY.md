# 电商 AI 客服 · 运行与部署指南

本文说明如何**接入内部大模型**、**模拟对话场景**并**自动质检**。

## 架构

```text
用户选择场景 / 输入问题
        │
        ▼
┌───────────────────┐     OpenAI 兼容协议      ┌────────────────────┐
│ DialogueDemoServer│ ───────────────────────► │ 内部大模型网关      │
│ 或 CLI --llm      │   /v1/chat/completions   │ (vLLM/Ollama/自建) │
└─────────┬─────────┘                          └────────────────────┘
          │ 客服回复文本
          ▼
┌───────────────────┐
│ ComplianceChecker │  ← 11 条可机检规范
└─────────┬─────────┘
          ▼
     质检报告 PASS/FAIL
```

## 1. 环境要求

- JDK 21+
- Maven Wrapper（仓库自带 `./mvnw`）
- 一个 **OpenAI Chat Completions 兼容** 的内部大模型端点  
  （Ollama / vLLM / 通义兼容模式 / 公司 LLM 网关均可）

## 2. 配置内部大模型

复制环境变量模板：

```bash
cd ecommerce-cs-skill
cp .env.example .env
```

| 变量 | 含义 | 示例 |
|------|------|------|
| `LLM_BASE_URL` | 兼容接口根路径（含 `/v1`） | `http://127.0.0.1:11434/v1` |
| `LLM_API_KEY` | Bearer Token；本地无鉴权可填 `local` | `local` |
| `LLM_MODEL` | 模型名 | `qwen2.5:7b` |
| `LLM_TIMEOUT_SECONDS` | 超时秒数 | `60` |
| `LLM_TEMPERATURE` | 采样温度 | `0.2` |
| `PORT` | Web 端口 | `8080` |

加载方式（任选）：

```bash
export $(grep -v '^#' .env | xargs)
# 或
set -a && source .env && set +a
```

### 常见内部模型接入示例

**Ollama（本机）**

```bash
ollama pull qwen2.5:7b
export LLM_BASE_URL=http://127.0.0.1:11434/v1
export LLM_API_KEY=local
export LLM_MODEL=qwen2.5:7b
```

**vLLM / 公司网关**

```bash
export LLM_BASE_URL=https://llm-gateway.internal.example.com/v1
export LLM_API_KEY=sk-xxxx
export LLM_MODEL=qwen2.5-72b-instruct
```

**本地 Mock 网关（无真实 GPU 时验证链路）**

```bash
python3 deploy/mock_internal_llm.py --port 18080
export LLM_BASE_URL=http://127.0.0.1:18080/v1
export LLM_API_KEY=local
export LLM_MODEL=mock-internal-qwen
```

## 3. 构建

```bash
cd ecommerce-cs-skill
./mvnw -q test
./mvnw -q -DskipTests package
```

产物：`target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar`

## 4. 模拟对话场景的三种方式

### 方式 A：Web 演示台（推荐展示）

```bash
export LLM_BASE_URL=... LLM_API_KEY=... LLM_MODEL=...
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --serve 8080
```

浏览器打开：<http://127.0.0.1:8080/>

操作：

1. 左侧选择场景（运输中 / 物流异常 / 缺订单号 …）
2. 点击 **「调用真实 LLM 并质检」**
3. 右侧查看客服回复 + 逐条规范 PASS/FAIL
4. 也可点「规则模板合规回复」做对照，或粘贴任意话术「仅质检」

### 方式 B：命令行单场景

```bash
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --list
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --llm S01_IN_TRANSIT
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --llm S06_LOGISTICS_EXCEPTION
```

### 方式 C：全场景 LLM 质检回归

```bash
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --llm-regression
```

退出码：`0` 全过，`2` 存在质检失败，`1` LLM 连接失败。

### 不依赖 LLM 的模板回归（CI 可用）

```bash
java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --regression
```

## 5. HTTP API（便于联调）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 服务与 LLM 配置 |
| GET | `/api/scenarios` | 场景列表 |
| POST | `/api/simulate/llm` | `{"scenarioId":"S01_IN_TRANSIT"}` → LLM 回复 + 质检 |
| POST | `/api/simulate/template` | 规则模板回复 + 质检 |
| POST | `/api/inspect` | `{"scenarioId":"...","reply":"..."}` 仅质检 |

示例：

```bash
curl -s http://127.0.0.1:8080/api/health | jq .
curl -s -X POST http://127.0.0.1:8080/api/simulate/llm \
  -H 'Content-Type: application/json' \
  -d '{"scenarioId":"S01_IN_TRANSIT"}' | jq .
```

## 6. Docker 部署

```bash
cd ecommerce-cs-skill
# 先保证宿主机或同网络内 LLM 可访问
docker compose -f deploy/docker-compose.yml up --build -d
```

默认映射 `8080:8080`。通过 `deploy/docker-compose.yml` 中的 `LLM_*` 环境变量指向内部模型。

若使用 compose 内附带的 mock LLM：

```bash
docker compose -f deploy/docker-compose.yml --profile mock up --build -d
# 此时 app 的 LLM_BASE_URL 指向 mock-llm:18080
```

## 7. 代码入口速查

| 类 | 作用 |
|----|------|
| `OpenAiCompatibleLlmClient` | 调用内部大模型 |
| `LlmCustomerServiceAgent` | 组装 prompt 并生成客服回复 |
| `LlmQualityInspectionService` | LLM 回复 → 规范质检 |
| `DialogueDemoServer` | Web/API 演示 |
| `EcommerceCsSkillMain` | CLI 入口 |

## 8. 故障排查

| 现象 | 处理 |
|------|------|
| `无法连接 LLM` | 检查 `LLM_BASE_URL` 是否可达；公司网关是否需 VPN |
| HTTP 401/403 | 检查 `LLM_API_KEY` |
| HTTP 404 | 确认路径含 `/v1`，完整 URL 为 `{BASE}/chat/completions` |
| 质检常失败 | 查看报告失败项；可收紧 system prompt 或调整温度 `LLM_TEMPERATURE=0.1` |
| 页面打不开 | 确认 `--serve` 已启动且端口未占用 |
