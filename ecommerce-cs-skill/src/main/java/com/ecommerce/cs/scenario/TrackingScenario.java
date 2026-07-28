package com.ecommerce.cs.scenario;

import com.ecommerce.cs.model.CustomerInquiry;
import com.ecommerce.cs.model.Order;

import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * 一个可复现的对话场景：订单事实 + 用户提问 + 期望命中的规范项。
 */
public final class TrackingScenario {
    private final String id;
    private final String name;
    private final String description;
    private final Order order;
    private final CustomerInquiry inquiry;
    /** 该场景下回复必须满足的规范编码；空表示“仅需通用规范”。 */
    private final Set<String> requiredRuleIds;
    /** 该场景下特别敏感、常被违反的规范编码（用于负面样例断言）。 */
    private final Set<String> criticalRuleIds;

    public TrackingScenario(
            String id,
            String name,
            String description,
            Order order,
            CustomerInquiry inquiry,
            Set<String> requiredRuleIds,
            Set<String> criticalRuleIds) {
        this.id = Objects.requireNonNull(id, "id");
        this.name = Objects.requireNonNull(name, "name");
        this.description = Objects.requireNonNull(description, "description");
        this.order = order;
        this.inquiry = Objects.requireNonNull(inquiry, "inquiry");
        this.requiredRuleIds = Set.copyOf(requiredRuleIds);
        this.criticalRuleIds = Set.copyOf(criticalRuleIds);
    }

    public String id() {
        return id;
    }

    public String name() {
        return name;
    }

    public String description() {
        return description;
    }

    public Order order() {
        return order;
    }

    public CustomerInquiry inquiry() {
        return inquiry;
    }

    public Set<String> requiredRuleIds() {
        return requiredRuleIds;
    }

    public Set<String> criticalRuleIds() {
        return criticalRuleIds;
    }

    public boolean orderMissing() {
        return order == null;
    }

    public List<String> summaryLines() {
        return List.of(
                "场景ID: " + id,
                "名称: " + name,
                "说明: " + description,
                "用户消息: " + inquiry.message(),
                "订单号: " + (order == null ? "(无)" : order.orderId()),
                "状态: " + (order == null ? "(无)" : order.status().displayName())
        );
    }
}
