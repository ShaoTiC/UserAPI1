package com.ecommerce.cs.scenario;

import com.ecommerce.cs.compliance.ComplianceRuleIds;
import com.ecommerce.cs.model.CustomerInquiry;
import com.ecommerce.cs.model.LogisticsEvent;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.model.OrderStatus;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 内置订单进度追踪场景库，覆盖常见电商客服对话情况。
 */
public final class ScenarioCatalog {

    private final Map<String, TrackingScenario> scenarios;

    public ScenarioCatalog() {
        this.scenarios = buildDefaults().stream()
                .collect(Collectors.toUnmodifiableMap(TrackingScenario::id, Function.identity()));
    }

    public List<TrackingScenario> all() {
        return List.copyOf(scenarios.values());
    }

    public Optional<TrackingScenario> find(String id) {
        return Optional.ofNullable(scenarios.get(id));
    }

    public TrackingScenario require(String id) {
        return find(id).orElseThrow(() -> new IllegalArgumentException("未知场景: " + id));
    }

    private static List<TrackingScenario> buildDefaults() {
        LocalDateTime now = LocalDateTime.of(2026, 7, 28, 10, 0);

        Order inTransit = Order.builder()
                .orderId("TB20260728001")
                .userId("u1001")
                .productName("无线降噪耳机 Pro")
                .status(OrderStatus.IN_TRANSIT)
                .carrier("顺丰速运")
                .trackingNumber("SF1234567890")
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .estimatedDelivery(now.plusDays(1))
                .addLogisticsEvent(new LogisticsEvent(now.minusDays(2), "深圳", "商家已发货"))
                .addLogisticsEvent(new LogisticsEvent(now.minusDays(1), "广州转运中心", "快件已到达转运中心"))
                .addLogisticsEvent(new LogisticsEvent(now.minusHours(5), "杭州转运中心", "快件运输中"))
                .build();

        Order pendingPayment = Order.builder()
                .orderId("JD20260728002")
                .userId("u1001")
                .productName("机械键盘")
                .status(OrderStatus.PENDING_PAYMENT)
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .build();

        Order pendingShipment = Order.builder()
                .orderId("TB20260728003")
                .userId("u1001")
                .productName("夏季凉感四件套")
                .status(OrderStatus.PAID_PENDING_SHIPMENT)
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .estimatedDelivery(now.plusDays(3))
                .build();

        Order outForDelivery = Order.builder()
                .orderId("JD20260728004")
                .userId("u1001")
                .productName("空气炸锅")
                .status(OrderStatus.OUT_FOR_DELIVERY)
                .carrier("京东物流")
                .trackingNumber("JD9876543210")
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .estimatedDelivery(now.plusHours(6))
                .addLogisticsEvent(new LogisticsEvent(now.minusHours(2), "杭州西湖站", "快递员正在派送"))
                .build();

        Order delivered = Order.builder()
                .orderId("TB20260728005")
                .userId("u1001")
                .productName("运动跑鞋")
                .status(OrderStatus.DELIVERED)
                .carrier("圆通速递")
                .trackingNumber("YT555666777")
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .addLogisticsEvent(new LogisticsEvent(now.minusHours(20), "杭州", "快件已签收，签收人：本人"))
                .build();

        Order exception = Order.builder()
                .orderId("TB20260728006")
                .userId("u1001")
                .productName("蓝牙音箱")
                .status(OrderStatus.LOGISTICS_EXCEPTION)
                .carrier("中通快递")
                .trackingNumber("ZT1122334455")
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .exceptionReason("派送失败：收件人电话无人接听，快件已滞留网点")
                .addLogisticsEvent(new LogisticsEvent(now.minusDays(1), "杭州网点", "派送失败，联系不上收件人"))
                .build();

        Order returning = Order.builder()
                .orderId("JD20260728007")
                .userId("u1001")
                .productName("智能手表")
                .status(OrderStatus.RETURNING)
                .carrier("德邦快递")
                .trackingNumber("DB7788990011")
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .addLogisticsEvent(new LogisticsEvent(now.minusHours(8), "杭州", "退货包裹已揽收"))
                .build();

        Order refunded = Order.builder()
                .orderId("TB20260728008")
                .userId("u1001")
                .productName("保温杯")
                .status(OrderStatus.REFUNDED)
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .build();

        Order cancelled = Order.builder()
                .orderId("JD20260728009")
                .userId("u1001")
                .productName("桌面支架")
                .status(OrderStatus.CANCELLED)
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .build();

        Order delayedShipment = Order.builder()
                .orderId("TB20260728010")
                .userId("u1001")
                .productName("露营帐篷")
                .status(OrderStatus.PAID_PENDING_SHIPMENT)
                .receiverName("张三")
                .receiverPhone("13812345678")
                .receiverAddress("浙江省杭州市西湖区文三路100号")
                .exceptionReason("超出售后承诺发货时效 48 小时，商家尚未揽收")
                .estimatedDelivery(now.plusDays(5))
                .build();

        return List.of(
                scenario(
                        "S01_IN_TRANSIT",
                        "运输中正常查询",
                        "用户提供订单号查询在途包裹进度",
                        inTransit,
                        new CustomerInquiry("u1001", "帮我查一下订单 TB20260728001 现在到哪了？", "TB20260728001"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.TRACKING_COMPLETENESS,
                                ComplianceRuleIds.PRIVACY_MASKING,
                                ComplianceRuleIds.POLITENESS,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION, ComplianceRuleIds.PRIVACY_MASKING)
                ),
                scenario(
                        "S02_PENDING_PAYMENT",
                        "待付款查询",
                        "订单尚未支付，应引导去支付而非编造物流",
                        pendingPayment,
                        new CustomerInquiry("u1001", "我的机械键盘怎么还没发货？订单 JD20260728002", "JD20260728002"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP,
                                ComplianceRuleIds.NO_FABRICATION
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S03_PENDING_SHIPMENT",
                        "已付款待发货",
                        "已支付但商家未发货，应说明备货并给出预计发货/到达信息",
                        pendingShipment,
                        new CustomerInquiry("u1001", "订单 TB20260728003 什么时候发货？", "TB20260728003"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP,
                                ComplianceRuleIds.NO_OVERPROMISE
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S04_OUT_FOR_DELIVERY",
                        "派送中",
                        "快递员正在派送，应告知派送状态与联系建议",
                        outForDelivery,
                        new CustomerInquiry("u1001", "今天能送到吗？订单 JD20260728004", "JD20260728004"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.TRACKING_COMPLETENESS,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.PRIVACY_MASKING)
                ),
                scenario(
                        "S05_DELIVERED",
                        "已签收",
                        "包裹已签收，应确认签收并引导售后/评价而非继续催物流",
                        delivered,
                        new CustomerInquiry("u1001", "我的跑鞋到了吗？TB20260728005", "TB20260728005"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S06_LOGISTICS_EXCEPTION",
                        "物流异常滞留",
                        "派送失败，应说明原因、脱敏联系方式，并提供改约/催派/升级路径",
                        exception,
                        new CustomerInquiry("u1001", "音箱怎么一直没动静？TB20260728006", "TB20260728006"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.EXCEPTION_HANDLING,
                                ComplianceRuleIds.PRIVACY_MASKING,
                                ComplianceRuleIds.ESCALATION_PATH,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.EXCEPTION_HANDLING, ComplianceRuleIds.ESCALATION_PATH)
                ),
                scenario(
                        "S07_MISSING_ORDER_ID",
                        "未提供订单号",
                        "用户只说查物流，未给订单号，应先索取订单号，不得臆测订单",
                        null,
                        new CustomerInquiry("u1001", "帮我查一下快递到哪了"),
                        Set.of(
                                ComplianceRuleIds.ORDER_ID_REQUIRED,
                                ComplianceRuleIds.NO_FABRICATION,
                                ComplianceRuleIds.POLITENESS
                        ),
                        Set.of(ComplianceRuleIds.ORDER_ID_REQUIRED, ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S08_ORDER_NOT_FOUND",
                        "订单不存在或不属于用户",
                        "查无此单或无权查看，应明确告知且不泄露其他用户信息",
                        null,
                        new CustomerInquiry("u1001", "查一下订单号 FAKE000000", "FAKE000000"),
                        Set.of(
                                ComplianceRuleIds.ORDER_NOT_FOUND_HANDLING,
                                ComplianceRuleIds.PRIVACY_MASKING,
                                ComplianceRuleIds.POLITENESS
                        ),
                        Set.of(ComplianceRuleIds.ORDER_NOT_FOUND_HANDLING)
                ),
                scenario(
                        "S09_RETURNING",
                        "退货运输中",
                        "退货包裹在途，应说明退货物流进度与退款节点",
                        returning,
                        new CustomerInquiry("u1001", "我退的手表寄到哪里了？JD20260728007", "JD20260728007"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.TRACKING_COMPLETENESS,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.STATUS_ACCURACY)
                ),
                scenario(
                        "S10_REFUNDED",
                        "已退款完成",
                        "退款已完成，应确认结果并提示到账时效，不编造物流",
                        refunded,
                        new CustomerInquiry("u1001", "退款到账了吗？TB20260728008", "TB20260728008"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP,
                                ComplianceRuleIds.NO_FABRICATION
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S11_CANCELLED",
                        "订单已取消",
                        "订单取消后不应再承诺发货",
                        cancelled,
                        new CustomerInquiry("u1001", "支架什么时候发？JD20260728009", "JD20260728009"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP,
                                ComplianceRuleIds.NO_FABRICATION
                        ),
                        Set.of(ComplianceRuleIds.NO_FABRICATION)
                ),
                scenario(
                        "S12_DELAYED_SHIPMENT",
                        "超时未发货",
                        "超出发货时效，应致歉、说明原因并提供催发货/取消/赔付指引",
                        delayedShipment,
                        new CustomerInquiry("u1001", "帐篷买了两天还不发货！TB20260728010", "TB20260728010"),
                        Set.of(
                                ComplianceRuleIds.STATUS_ACCURACY,
                                ComplianceRuleIds.EXCEPTION_HANDLING,
                                ComplianceRuleIds.ESCALATION_PATH,
                                ComplianceRuleIds.POLITENESS,
                                ComplianceRuleIds.ACTIONABLE_NEXT_STEP
                        ),
                        Set.of(ComplianceRuleIds.EXCEPTION_HANDLING, ComplianceRuleIds.ESCALATION_PATH)
                )
        );
    }

    private static TrackingScenario scenario(
            String id,
            String name,
            String description,
            Order order,
            CustomerInquiry inquiry,
            Set<String> required,
            Set<String> critical) {
        return new TrackingScenario(id, name, description, order, inquiry, required, critical);
    }
}
