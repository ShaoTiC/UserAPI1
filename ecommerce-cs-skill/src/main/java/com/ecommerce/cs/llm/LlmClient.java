package com.ecommerce.cs.llm;

/**
 * 大模型聊天客户端抽象。
 */
public interface LlmClient {

    /**
     * 发送一轮对话，返回助手文本内容。
     */
    String chat(String systemPrompt, String userPrompt);

    /**
     * 当前使用的模型标识（用于日志/报告）。
     */
    String modelName();
}
