package com.ecommerce.cs.web;

import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.compliance.RuleCheckResult;
import com.ecommerce.cs.llm.LlmConfig;
import com.ecommerce.cs.llm.LlmCustomerServiceAgent;
import com.ecommerce.cs.llm.LlmException;
import com.ecommerce.cs.llm.LlmInspectionResult;
import com.ecommerce.cs.llm.LlmQualityInspectionService;
import com.ecommerce.cs.llm.OpenAiCompatibleLlmClient;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.TrackingScenario;
import com.ecommerce.cs.skill.EcommerceOrderTrackingSkill;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

/**
 * 轻量 HTTP 演示服务：场景列表 / LLM 对话质检 / 规则模板对照。
 */
public final class DialogueDemoServer {

    private final int port;
    private final EcommerceOrderTrackingSkill skill;
    private final LlmQualityInspectionService llmInspection;
    private final LlmConfig llmConfig;

    public DialogueDemoServer(int port) {
        this.port = port;
        this.skill = new EcommerceOrderTrackingSkill();
        this.llmConfig = LlmConfig.fromEnv();
        this.llmInspection = new LlmQualityInspectionService(
                skill.catalog(),
                new LlmCustomerServiceAgent(new OpenAiCompatibleLlmClient(llmConfig)),
                new com.ecommerce.cs.compliance.ComplianceChecker());
    }

    public void start() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", this::handleIndex);
        server.createContext("/api/health", this::handleHealth);
        server.createContext("/api/scenarios", this::handleScenarios);
        server.createContext("/api/simulate/template", this::handleTemplateSimulate);
        server.createContext("/api/simulate/llm", this::handleLlmSimulate);
        server.createContext("/api/inspect", this::handleInspectExternal);
        server.setExecutor(Executors.newCachedThreadPool());
        server.start();
        System.out.println("电商 AI 客服演示已启动: http://127.0.0.1:" + port + "/");
        System.out.println("LLM 配置: " + llmConfig);
    }

    private void handleIndex(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            send(exchange, 405, "text/plain; charset=utf-8", "Method Not Allowed");
            return;
        }
        byte[] html = readClasspathResource("/web/index.html");
        sendBytes(exchange, 200, "text/html; charset=utf-8", html);
    }

    private void handleHealth(HttpExchange exchange) throws IOException {
        String body = """
                {"ok":true,"llmBaseUrl":%s,"llmModel":%s}
                """.formatted(jsonStr(llmConfig.baseUrl()), jsonStr(llmConfig.model()));
        sendJson(exchange, 200, body);
    }

    private void handleScenarios(HttpExchange exchange) throws IOException {
        String items = skill.catalog().all().stream()
                .sorted((a, b) -> a.id().compareTo(b.id()))
                .map(s -> """
                        {"id":%s,"name":%s,"description":%s,"userMessage":%s,"orderId":%s,"status":%s}
                        """.formatted(
                        jsonStr(s.id()),
                        jsonStr(s.name()),
                        jsonStr(s.description()),
                        jsonStr(s.inquiry().message()),
                        jsonStr(s.order() == null ? "" : s.order().orderId()),
                        jsonStr(s.order() == null ? "" : s.order().status().displayName())
                ).trim())
                .collect(Collectors.joining(","));
        sendJson(exchange, 200, "{\"scenarios\":[" + items + "]}");
    }

    private void handleTemplateSimulate(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            send(exchange, 405, "text/plain; charset=utf-8", "Method Not Allowed");
            return;
        }
        Map<String, String> body = parseJsonObject(readBody(exchange));
        String scenarioId = body.getOrDefault("scenarioId", "S01_IN_TRANSIT");
        boolean nonCompliant = Boolean.parseBoolean(body.getOrDefault("nonCompliant", "false"));
        TrackingScenario scenario = skill.catalog().require(scenarioId);
        AgentReply reply = nonCompliant
                ? skill.simulateNonCompliantReply(scenarioId)
                : skill.simulateCompliantReply(scenarioId);
        ComplianceReport report = skill.evaluate(scenario, reply);
        sendJson(exchange, 200, toInspectionJson("template", "rules-engine", scenario, reply, report));
    }

    private void handleLlmSimulate(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            send(exchange, 405, "text/plain; charset=utf-8", "Method Not Allowed");
            return;
        }
        Map<String, String> body = parseJsonObject(readBody(exchange));
        String scenarioId = body.getOrDefault("scenarioId", "S01_IN_TRANSIT");
        try {
            LlmInspectionResult result = llmInspection.inspectScenario(scenarioId);
            sendJson(exchange, 200, toInspectionJson(
                    "llm",
                    result.modelName(),
                    result.scenario(),
                    result.reply(),
                    result.report()));
        } catch (LlmException ex) {
            sendJson(exchange, 502, "{\"error\":" + jsonStr(ex.getMessage()) + "}");
        }
    }

    private void handleInspectExternal(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            send(exchange, 405, "text/plain; charset=utf-8", "Method Not Allowed");
            return;
        }
        Map<String, String> body = parseJsonObject(readBody(exchange));
        String scenarioId = body.getOrDefault("scenarioId", "S01_IN_TRANSIT");
        String replyText = body.getOrDefault("reply", "");
        TrackingScenario scenario = skill.catalog().require(scenarioId);
        AgentReply reply = new AgentReply(replyText, AgentReply.ReplySource.EXTERNAL);
        ComplianceReport report = skill.evaluate(scenario, reply);
        sendJson(exchange, 200, toInspectionJson("external", "manual", scenario, reply, report));
    }

    private String toInspectionJson(
            String mode,
            String model,
            TrackingScenario scenario,
            AgentReply reply,
            ComplianceReport report) {
        String rules = report.results().stream()
                .map(this::ruleJson)
                .collect(Collectors.joining(","));
        return """
                {
                  "mode":%s,
                  "model":%s,
                  "scenarioId":%s,
                  "scenarioName":%s,
                  "userMessage":%s,
                  "reply":%s,
                  "passed":%s,
                  "rules":[%s]
                }
                """.formatted(
                jsonStr(mode),
                jsonStr(model),
                jsonStr(scenario.id()),
                jsonStr(scenario.name()),
                jsonStr(scenario.inquiry().message()),
                jsonStr(reply.content()),
                report.allPassed(),
                rules
        );
    }

    private String ruleJson(RuleCheckResult r) {
        return """
                {"id":%s,"name":%s,"passed":%s,"detail":%s}
                """.formatted(
                jsonStr(r.ruleId()),
                jsonStr(r.ruleName()),
                r.passed(),
                jsonStr(r.detail())
        ).trim();
    }

    private static byte[] readClasspathResource(String path) throws IOException {
        try (InputStream in = DialogueDemoServer.class.getResourceAsStream(path)) {
            if (in == null) {
                throw new IOException("缺少资源: " + path);
            }
            return in.readAllBytes();
        }
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static void sendJson(HttpExchange exchange, int code, String body) throws IOException {
        send(exchange, code, "application/json; charset=utf-8", body);
    }

    private static void send(HttpExchange exchange, int code, String contentType, String body) throws IOException {
        sendBytes(exchange, code, contentType, body.getBytes(StandardCharsets.UTF_8));
    }

    private static void sendBytes(HttpExchange exchange, int code, String contentType, byte[] bytes) throws IOException {
        Headers headers = exchange.getResponseHeaders();
        headers.set("Content-Type", contentType);
        headers.set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    static String jsonStr(String raw) {
        if (raw == null) {
            return "null";
        }
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < raw.length(); i++) {
            char c = raw.charAt(i);
            switch (c) {
                case '\\' -> sb.append("\\\\");
                case '"' -> sb.append("\\\"");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                }
            }
        }
        return sb.append('"').toString();
    }

    /**
     * 极简 JSON object 解析（仅支持扁平 string/boolean 字段，满足本演示 API）。
     */
    static Map<String, String> parseJsonObject(String json) {
        Map<String, String> map = new HashMap<>();
        if (json == null || json.isBlank()) {
            return map;
        }
        String trimmed = json.trim();
        if (!trimmed.startsWith("{")) {
            return map;
        }
        // "key":"value" or "key":true/false
        java.util.regex.Matcher m = java.util.regex.Pattern
                .compile("\"([^\"]+)\"\\s*:\\s*(\"(?:\\\\.|[^\"\\\\])*\"|true|false)")
                .matcher(trimmed);
        while (m.find()) {
            String key = m.group(1);
            String rawVal = m.group(2);
            if (rawVal.startsWith("\"")) {
                map.put(key, OpenAiCompatibleLlmClient.unescapeJson(rawVal.substring(1, rawVal.length() - 1)));
            } else {
                map.put(key, rawVal);
            }
        }
        return map;
    }

    public static void main(String[] args) throws IOException {
        int port = 8080;
        if (args.length > 0) {
            port = Integer.parseInt(args[0]);
        } else if (System.getenv("PORT") != null && !System.getenv("PORT").isBlank()) {
            port = Integer.parseInt(System.getenv("PORT"));
        }
        new DialogueDemoServer(port).start();
    }
}
