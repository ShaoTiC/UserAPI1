package com.ecommerce.cs.service;

import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.model.CustomerInquiry;
import com.ecommerce.cs.model.LogisticsEvent;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.model.OrderStatus;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * 合规模拟 AI 客服：基于订单事实生成符合规范的进度回复。
 */
public final class CompliantCustomerServiceAgent {

    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

    private final Map<String, Order> orderIndex = new HashMap<>();

    public CompliantCustomerServiceAgent() {
    }

    public CompliantCustomerServiceAgent register(Order order) {
        orderIndex.put(order.orderId(), order);
        return this;
    }

    public CompliantCustomerServiceAgent registerAll(Iterable<Order> orders) {
        for (Order order : orders) {
            register(order);
        }
        return this;
    }

    public AgentReply reply(TrackingScenario scenario) {
        if (scenario.order() != null) {
            register(scenario.order());
        }
        return reply(scenario.inquiry(), Optional.ofNullable(scenario.order()));
    }

    public AgentReply reply(CustomerInquiry inquiry, Optional<Order> knownOrder) {
        Optional<String> orderId = inquiry.providedOrderId();
        if (orderId.isEmpty()) {
            return new AgentReply(
                    "您好，为帮您准确查询物流进度，请提供订单号（可在「我的订单」中复制）。"
                            + "提供后我会为您核对状态、承运商与最新轨迹。",
                    AgentReply.ReplySource.COMPLIANT_SIMULATOR
            );
        }

        Order order = knownOrder.orElseGet(() -> orderIndex.get(orderId.get()));
        if (order == null || !order.userId().equals(inquiry.userId())) {
            return new AgentReply(
                    "您好，未找到订单号 " + orderId.get() + " 的可查询记录。"
                            + "请核对订单号是否正确，或确认该订单属于当前账号；"
                            + "如仍有问题可转人工客服协助。",
                    AgentReply.ReplySource.COMPLIANT_SIMULATOR
            );
        }

        return new AgentReply(buildStatusReply(order), AgentReply.ReplySource.COMPLIANT_SIMULATOR);
    }

    private String buildStatusReply(Order order) {
        StringBuilder sb = new StringBuilder();
        sb.append("您好，已为您查询到订单 ").append(order.orderId())
                .append("（").append(order.productName()).append("），")
                .append("当前状态：").append(order.status().displayName()).append("。");

        if (order.receiverPhone() != null) {
            sb.append("收件人手机：").append(Order.maskPhone(order.receiverPhone())).append("；");
        }
        if (order.receiverAddress() != null) {
            sb.append("收货地址：").append(Order.maskAddress(order.receiverAddress())).append("。");
        }

        switch (order.status()) {
            case PENDING_PAYMENT -> sb.append("订单尚未支付，请尽快完成支付；超时未付可能会自动取消。");
            case PAID_PENDING_SHIPMENT -> {
                sb.append("商家正在备货，暂无运单信息。");
                if (order.exceptionReason() != null) {
                    sb.append("抱歉，").append(order.exceptionReason()).append("。");
                    sb.append("您可以催发货、取消订单，或转人工升级处理/申请赔付指引。");
                } else {
                    sb.append("请耐心等待商家揽收；如超时未发货可催发货或取消订单。");
                    if (order.estimatedDelivery() != null) {
                        sb.append("参考预计送达：").append(TIME_FMT.format(order.estimatedDelivery())).append("（以实际物流为准）。");
                    }
                }
            }
            case SHIPPED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, LOGISTICS_EXCEPTION, RETURNING -> {
                sb.append("承运商：").append(order.carrier())
                        .append("，运单号：").append(order.trackingNumber()).append("。");
                latestEvent(order).ifPresent(event ->
                        sb.append("最新轨迹：").append(TIME_FMT.format(event.time()))
                                .append(" ").append(event.description()).append("。"));
                appendStatusSpecificGuidance(order, sb);
            }
            case REFUNDED -> sb.append("退款已完成，款项将原路退回，请留意账单到账情况；如超时未到账可提供支付凭证转人工核查。");
            case CANCELLED -> sb.append("该订单已取消，不会再发货。如仍需商品请重新下单。");
        }
        sb.append("感谢您的耐心，还有疑问随时告诉我。");
        return sb.toString();
    }

    private void appendStatusSpecificGuidance(Order order, StringBuilder sb) {
        switch (order.status()) {
            case SHIPPED, IN_TRANSIT -> {
                sb.append("包裹运输中，请持续关注物流详情；签收前请当面核对。如轨迹长时间无更新可联系客服。");
                if (order.estimatedDelivery() != null) {
                    sb.append("预计送达参考：").append(TIME_FMT.format(order.estimatedDelivery())).append("（非保证时效）。");
                }
            }
            case OUT_FOR_DELIVERY -> sb.append("快递员正在派送，请保持电话畅通；如需代收或改派可联系快递员。");
            case DELIVERED -> sb.append("包裹已签收。若非本人签收或商品异常，可申请售后；也可对本次服务进行评价。");
            case LOGISTICS_EXCEPTION -> {
                sb.append("当前存在物流异常");
                if (order.exceptionReason() != null) {
                    sb.append("：").append(order.exceptionReason());
                }
                sb.append("。建议更新收件电话、申请改约派送或催派，也可转人工升级处理。");
            }
            case RETURNING -> sb.append("退货包裹运输中，商家签收后将进入退款审核，请关注退货进度与退款结果。");
            default -> {
            }
        }
    }

    private Optional<LogisticsEvent> latestEvent(Order order) {
        return order.logisticsTrail().stream().max(Comparator.comparing(LogisticsEvent::time));
    }
}
