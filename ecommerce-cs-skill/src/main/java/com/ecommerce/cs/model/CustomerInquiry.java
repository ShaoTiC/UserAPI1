package com.ecommerce.cs.model;

import java.util.Objects;
import java.util.Optional;

/**
 * 用户向 AI 客服发起的一次查询上下文。
 */
public final class CustomerInquiry {
    private final String userId;
    private final String message;
    private final String providedOrderId;

    public CustomerInquiry(String userId, String message) {
        this(userId, message, null);
    }

    public CustomerInquiry(String userId, String message, String providedOrderId) {
        this.userId = Objects.requireNonNull(userId, "userId");
        this.message = Objects.requireNonNull(message, "message");
        this.providedOrderId = providedOrderId;
    }

    public String userId() {
        return userId;
    }

    public String message() {
        return message;
    }

    public Optional<String> providedOrderId() {
        return Optional.ofNullable(providedOrderId).filter(id -> !id.isBlank());
    }
}
