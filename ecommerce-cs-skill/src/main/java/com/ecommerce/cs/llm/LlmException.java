package com.ecommerce.cs.llm;

/**
 * 调用内部大模型失败时抛出。
 */
public final class LlmException extends RuntimeException {

    public LlmException(String message) {
        super(message);
    }

    public LlmException(String message, Throwable cause) {
        super(message, cause);
    }
}
