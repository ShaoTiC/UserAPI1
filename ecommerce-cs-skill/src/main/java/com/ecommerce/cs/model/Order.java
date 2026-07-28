package com.ecommerce.cs.model;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * 订单快照：客服查询与规范检测的事实来源。
 */
public final class Order {
    private final String orderId;
    private final String userId;
    private final String productName;
    private final OrderStatus status;
    private final String carrier;
    private final String trackingNumber;
    private final String receiverName;
    private final String receiverPhone;
    private final String receiverAddress;
    private final LocalDateTime estimatedDelivery;
    private final String exceptionReason;
    private final List<LogisticsEvent> logisticsTrail;

    private Order(Builder builder) {
        this.orderId = Objects.requireNonNull(builder.orderId, "orderId");
        this.userId = Objects.requireNonNull(builder.userId, "userId");
        this.productName = Objects.requireNonNull(builder.productName, "productName");
        this.status = Objects.requireNonNull(builder.status, "status");
        this.carrier = builder.carrier;
        this.trackingNumber = builder.trackingNumber;
        this.receiverName = builder.receiverName;
        this.receiverPhone = builder.receiverPhone;
        this.receiverAddress = builder.receiverAddress;
        this.estimatedDelivery = builder.estimatedDelivery;
        this.exceptionReason = builder.exceptionReason;
        this.logisticsTrail = List.copyOf(builder.logisticsTrail);
    }

    public String orderId() {
        return orderId;
    }

    public String userId() {
        return userId;
    }

    public String productName() {
        return productName;
    }

    public OrderStatus status() {
        return status;
    }

    public String carrier() {
        return carrier;
    }

    public String trackingNumber() {
        return trackingNumber;
    }

    public String receiverName() {
        return receiverName;
    }

    public String receiverPhone() {
        return receiverPhone;
    }

    public String receiverAddress() {
        return receiverAddress;
    }

    public LocalDateTime estimatedDelivery() {
        return estimatedDelivery;
    }

    public String exceptionReason() {
        return exceptionReason;
    }

    public List<LogisticsEvent> logisticsTrail() {
        return logisticsTrail;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String userId;
        private String productName;
        private OrderStatus status;
        private String carrier;
        private String trackingNumber;
        private String receiverName;
        private String receiverPhone;
        private String receiverAddress;
        private LocalDateTime estimatedDelivery;
        private String exceptionReason;
        private final List<LogisticsEvent> logisticsTrail = new ArrayList<>();

        public Builder orderId(String orderId) {
            this.orderId = orderId;
            return this;
        }

        public Builder userId(String userId) {
            this.userId = userId;
            return this;
        }

        public Builder productName(String productName) {
            this.productName = productName;
            return this;
        }

        public Builder status(OrderStatus status) {
            this.status = status;
            return this;
        }

        public Builder carrier(String carrier) {
            this.carrier = carrier;
            return this;
        }

        public Builder trackingNumber(String trackingNumber) {
            this.trackingNumber = trackingNumber;
            return this;
        }

        public Builder receiverName(String receiverName) {
            this.receiverName = receiverName;
            return this;
        }

        public Builder receiverPhone(String receiverPhone) {
            this.receiverPhone = receiverPhone;
            return this;
        }

        public Builder receiverAddress(String receiverAddress) {
            this.receiverAddress = receiverAddress;
            return this;
        }

        public Builder estimatedDelivery(LocalDateTime estimatedDelivery) {
            this.estimatedDelivery = estimatedDelivery;
            return this;
        }

        public Builder exceptionReason(String exceptionReason) {
            this.exceptionReason = exceptionReason;
            return this;
        }

        public Builder addLogisticsEvent(LogisticsEvent event) {
            this.logisticsTrail.add(event);
            return this;
        }

        public Builder logisticsTrail(List<LogisticsEvent> events) {
            this.logisticsTrail.clear();
            if (events != null) {
                this.logisticsTrail.addAll(events);
            }
            return this;
        }

        public Order build() {
            return new Order(this);
        }
    }

    /** 脱敏手机号，如 138****5678。 */
    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) {
            return phone == null ? "" : phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }

    /** 脱敏地址，仅保留省市与末尾门牌提示。 */
    public static String maskAddress(String address) {
        if (address == null || address.isBlank()) {
            return "";
        }
        if (address.length() <= 6) {
            return address.charAt(0) + "***";
        }
        return address.substring(0, Math.min(6, address.length())) + "***";
    }

    public List<String> knownLogisticsDescriptions() {
        List<String> descriptions = new ArrayList<>(logisticsTrail.size());
        for (LogisticsEvent event : logisticsTrail) {
            descriptions.add(event.description());
        }
        return Collections.unmodifiableList(descriptions);
    }
}
