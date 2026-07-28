package com.ecommerce.cs.llm;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * OpenAI Chat Completions 兼容客户端（内部大模型网关常用协议）。
 * <p>
 * 不依赖第三方 JSON 库，使用轻量解析提取 {@code choices[0].message.content}。
 */
public final class OpenAiCompatibleLlmClient implements LlmClient {

    private static final Pattern CONTENT_PATTERN = Pattern.compile(
            "\"content\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");
    private static final Pattern ERROR_PATTERN = Pattern.compile(
            "\"message\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");

    private final LlmConfig config;
    private final HttpClient httpClient;

    public OpenAiCompatibleLlmClient(LlmConfig config) {
        this.config = Objects.requireNonNull(config, "config");
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(config.timeout())
                .build();
    }

    @Override
    public String modelName() {
        return config.model();
    }

    @Override
    public String chat(String systemPrompt, String userPrompt) {
        Objects.requireNonNull(systemPrompt, "systemPrompt");
        Objects.requireNonNull(userPrompt, "userPrompt");

        String body = """
                {
                  "model": %s,
                  "temperature": %s,
                  "messages": [
                    {"role": "system", "content": %s},
                    {"role": "user", "content": %s}
                  ]
                }
                """.formatted(
                jsonString(config.model()),
                config.temperature(),
                jsonString(systemPrompt),
                jsonString(userPrompt)
        );

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(config.chatCompletionsUrl()))
                .timeout(config.timeout())
                .header("Content-Type", "application/json; charset=utf-8")
                .header("Authorization", "Bearer " + config.apiKey())
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new LlmException("LLM HTTP " + response.statusCode() + ": " + extractError(response.body()));
            }
            return extractAssistantContent(response.body());
        } catch (IOException e) {
            throw new LlmException("无法连接 LLM（" + config.chatCompletionsUrl()
                    + "）。请确认内部大模型已启动，并检查 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。原因: "
                    + e.getMessage(), e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new LlmException("调用 LLM 被中断", e);
        }
    }

    static String extractAssistantContent(String responseBody) {
        // 优先取 message.content；OpenAI 兼容响应中第一个 content 通常是助手回复
        Matcher matcher = CONTENT_PATTERN.matcher(responseBody);
        String lastContent = null;
        while (matcher.find()) {
            lastContent = unescapeJson(matcher.group(1));
        }
        if (lastContent == null || lastContent.isBlank()) {
            throw new LlmException("LLM 响应中未找到 message.content: " + truncate(responseBody, 400));
        }
        return lastContent.trim();
    }

    private static String extractError(String body) {
        Matcher matcher = ERROR_PATTERN.matcher(body == null ? "" : body);
        if (matcher.find()) {
            return unescapeJson(matcher.group(1));
        }
        return truncate(body == null ? "" : body, 300);
    }

    static String jsonString(String raw) {
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
        sb.append('"');
        return sb.toString();
    }

    public static String unescapeJson(String escaped) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < escaped.length(); i++) {
            char c = escaped.charAt(i);
            if (c == '\\' && i + 1 < escaped.length()) {
                char n = escaped.charAt(++i);
                switch (n) {
                    case 'n' -> sb.append('\n');
                    case 'r' -> sb.append('\r');
                    case 't' -> sb.append('\t');
                    case '"' -> sb.append('"');
                    case '\\' -> sb.append('\\');
                    case '/' -> sb.append('/');
                    case 'u' -> {
                        if (i + 4 < escaped.length()) {
                            String hex = escaped.substring(i + 1, i + 5);
                            sb.append((char) Integer.parseInt(hex, 16));
                            i += 4;
                        } else {
                            sb.append('u');
                        }
                    }
                    default -> sb.append(n);
                }
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    private static String truncate(String text, int max) {
        if (text.length() <= max) {
            return text;
        }
        return text.substring(0, max) + "...";
    }
}
