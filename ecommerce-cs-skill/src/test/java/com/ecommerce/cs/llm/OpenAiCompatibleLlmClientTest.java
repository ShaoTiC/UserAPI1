package com.ecommerce.cs.llm;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class OpenAiCompatibleLlmClientTest {

    @Test
    void extractsAssistantContent() {
        String body = """
                {"id":"1","choices":[{"message":{"role":"assistant","content":"您好，订单运输中。"}}]}
                """;
        assertEquals("您好，订单运输中。", OpenAiCompatibleLlmClient.extractAssistantContent(body));
    }

    @Test
    void jsonStringEscapes() {
        String json = OpenAiCompatibleLlmClient.jsonString("a\"b\nc");
        assertTrue(json.contains("\\\""));
        assertTrue(json.contains("\\n"));
    }
}
