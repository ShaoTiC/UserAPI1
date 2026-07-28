package com.ecommerce.cs.llm;

import java.time.Duration;
import java.util.Objects;
import java.util.Optional;

/**
 * OpenAI 兼容协议配置（适用于内部大模型网关 / vLLM / Ollama / 通义兼容模式等）。
 *
 * <p>环境变量：
 * <ul>
 *   <li>{@code LLM_BASE_URL} — 如 http://127.0.0.1:11434/v1 或 https://internal-llm.example.com/v1</li>
 *   <li>{@code LLM_API_KEY} — Bearer Token，无鉴权时可填任意非空值如 {@code local}</li>
 *   <li>{@code LLM_MODEL} — 模型名，如 qwen2.5:7b / gpt-4o-mini / deepseek-chat</li>
 *   <li>{@code LLM_TIMEOUT_SECONDS} — 可选，默认 60</li>
 *   <li>{@code LLM_TEMPERATURE} — 可选，默认 0.2</li>
 * </ul>
 */
public final class LlmConfig {

    private final String baseUrl;
    private final String apiKey;
    private final String model;
    private final Duration timeout;
    private final double temperature;

    public LlmConfig(String baseUrl, String apiKey, String model, Duration timeout, double temperature) {
        this.baseUrl = trimTrailingSlash(Objects.requireNonNull(baseUrl, "baseUrl"));
        this.apiKey = Objects.requireNonNull(apiKey, "apiKey");
        this.model = Objects.requireNonNull(model, "model");
        this.timeout = Objects.requireNonNull(timeout, "timeout");
        this.temperature = temperature;
    }

    public String baseUrl() {
        return baseUrl;
    }

    public String apiKey() {
        return apiKey;
    }

    public String model() {
        return model;
    }

    public Duration timeout() {
        return timeout;
    }

    public double temperature() {
        return temperature;
    }

    public String chatCompletionsUrl() {
        return baseUrl + "/chat/completions";
    }

    public boolean isConfigured() {
        return !baseUrl.isBlank() && !model.isBlank() && !apiKey.isBlank();
    }

    public static LlmConfig fromEnv() {
        String baseUrl = firstNonBlank(System.getenv("LLM_BASE_URL"), "http://127.0.0.1:11434/v1");
        String apiKey = firstNonBlank(System.getenv("LLM_API_KEY"), "local");
        String model = firstNonBlank(System.getenv("LLM_MODEL"), "qwen2.5:7b");
        int timeoutSec = parseInt(System.getenv("LLM_TIMEOUT_SECONDS"), 60);
        double temperature = parseDouble(System.getenv("LLM_TEMPERATURE"), 0.2);
        return new LlmConfig(baseUrl, apiKey, model, Duration.ofSeconds(timeoutSec), temperature);
    }

    public static Optional<LlmConfig> fromEnvIfPresent() {
        String baseUrl = System.getenv("LLM_BASE_URL");
        String model = System.getenv("LLM_MODEL");
        if ((baseUrl == null || baseUrl.isBlank()) && (model == null || model.isBlank())) {
            // 仍返回默认本地 Ollama 配置，便于一键对接内部/本地模型
            return Optional.of(fromEnv());
        }
        return Optional.of(fromEnv());
    }

    private static String firstNonBlank(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.trim();
    }

    private static int parseInt(String raw, int fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        return Integer.parseInt(raw.trim());
    }

    private static double parseDouble(String raw, double fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        return Double.parseDouble(raw.trim());
    }

    private static String trimTrailingSlash(String url) {
        if (url.endsWith("/")) {
            return url.substring(0, url.length() - 1);
        }
        return url;
    }

    @Override
    public String toString() {
        return "LlmConfig{baseUrl='%s', model='%s', timeout=%s, temperature=%s}"
                .formatted(baseUrl, model, timeout, temperature);
    }
}
