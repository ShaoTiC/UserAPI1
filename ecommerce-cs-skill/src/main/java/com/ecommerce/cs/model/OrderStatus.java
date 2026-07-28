package com.ecommerce.cs.model;

/**
 * 电商订单生命周期状态（物流进度追踪相关）。
 */
public enum OrderStatus {
    PENDING_PAYMENT("待付款"),
    PAID_PENDING_SHIPMENT("已付款待发货"),
    SHIPPED("已发货"),
    IN_TRANSIT("运输中"),
    OUT_FOR_DELIVERY("派送中"),
    DELIVERED("已签收"),
    LOGISTICS_EXCEPTION("物流异常"),
    RETURNING("退货中"),
    REFUNDED("已退款"),
    CANCELLED("已取消");

    private final String displayName;

    OrderStatus(String displayName) {
        this.displayName = displayName;
    }

    public String displayName() {
        return displayName;
    }

    public boolean hasTracking() {
        return this == SHIPPED
                || this == IN_TRANSIT
                || this == OUT_FOR_DELIVERY
                || this == DELIVERED
                || this == LOGISTICS_EXCEPTION
                || this == RETURNING;
    }

    public boolean isTerminal() {
        return this == DELIVERED || this == REFUNDED || this == CANCELLED;
    }
}
