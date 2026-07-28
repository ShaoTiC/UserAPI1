package com.ecommerce.cs.llm;

import com.ecommerce.cs.model.CustomerInquiry;
import com.ecommerce.cs.model.LogisticsEvent;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.stream.Collectors;

/**
 * 构造电商客服进度查询的 system / user prompt。
 */
public final class LlmPromptBuilder {

    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

    public String systemPrompt() {
        return """
                你是电商平台（类似淘宝/京东）的 AI 客服，专门回答用户关于订单与物流进度的问题。
                必须遵守以下规范：
                1. 只基于给定的「订单事实」回答，禁止编造运单号、轨迹节点、到达时间。
                2. 若缺少订单号，先礼貌索取订单号，不要臆测进度。
                3. 若查无订单，明确告知并请用户核对，不要编造物流。
                4. 已发货及之后状态必须说出承运商与运单号。
                5. 手机号、详细地址必须脱敏（如 138****5678；地址只保留省市前缀+***）。
                6. 语气礼貌专业，使用「您好」「请」「抱歉」等。
                7. 根据状态给出可执行下一步（支付/催发货/保持电话畅通/售后/转人工等）。
                8. 异常或超时未发货时说明原因，并提供催派/催发货/转人工等升级路径。
                9. 不要做「保证今天送达」「一定明天到」等无法兑现的承诺；预计时间需标注参考、非保证。
                10. 只输出给用户看的客服回复正文，不要输出分析过程或 JSON。
                """.stripIndent().trim();
    }

    public String userPrompt(TrackingScenario scenario) {
        StringBuilder sb = new StringBuilder();
        sb.append("【场景】").append(scenario.id()).append(" - ").append(scenario.name()).append('\n');
        sb.append("【场景说明】").append(scenario.description()).append('\n');
        sb.append("【用户消息】").append(scenario.inquiry().message()).append('\n');
        sb.append("【用户ID】").append(scenario.inquiry().userId()).append('\n');
        scenario.inquiry().providedOrderId().ifPresentOrElse(
                id -> sb.append("【用户提供的订单号】").append(id).append('\n'),
                () -> sb.append("【用户提供的订单号】（未提供）\n")
        );

        Order order = scenario.order();
        if (order == null) {
            if (scenario.inquiry().providedOrderId().isPresent()) {
                sb.append("【订单事实】系统中未找到该订单，或订单不属于当前用户。\n");
            } else {
                sb.append("【订单事实】尚无订单上下文，请先向用户索取订单号。\n");
            }
        } else {
            appendOrderFacts(sb, order);
        }
        sb.append("请生成一条符合规范的客服回复。");
        return sb.toString();
    }

    public String userPrompt(CustomerInquiry inquiry, Order order) {
        StringBuilder sb = new StringBuilder();
        sb.append("【用户消息】").append(inquiry.message()).append('\n');
        sb.append("【用户ID】").append(inquiry.userId()).append('\n');
        inquiry.providedOrderId().ifPresentOrElse(
                id -> sb.append("【用户提供的订单号】").append(id).append('\n'),
                () -> sb.append("【用户提供的订单号】（未提供）\n")
        );
        if (order == null) {
            if (inquiry.providedOrderId().isPresent()) {
                sb.append("【订单事实】系统中未找到该订单，或订单不属于当前用户。\n");
            } else {
                sb.append("【订单事实】尚无订单上下文，请先向用户索取订单号。\n");
            }
        } else {
            appendOrderFacts(sb, order);
        }
        sb.append("请生成一条符合规范的客服回复。");
        return sb.toString();
    }

    private void appendOrderFacts(StringBuilder sb, Order order) {
        sb.append("【订单事实】\n");
        sb.append("- 订单号: ").append(order.orderId()).append('\n');
        sb.append("- 商品: ").append(order.productName()).append('\n');
        sb.append("- 状态: ").append(order.status().displayName()).append('\n');
        if (order.carrier() != null) {
            sb.append("- 承运商: ").append(order.carrier()).append('\n');
        }
        if (order.trackingNumber() != null) {
            sb.append("- 运单号: ").append(order.trackingNumber()).append('\n');
        }
        if (order.receiverPhone() != null) {
            sb.append("- 收件手机(原始，回复时必须脱敏): ").append(order.receiverPhone()).append('\n');
        }
        if (order.receiverAddress() != null) {
            sb.append("- 收货地址(原始，回复时必须脱敏): ").append(order.receiverAddress()).append('\n');
        }
        if (order.estimatedDelivery() != null) {
            sb.append("- 预计送达(参考): ").append(TIME_FMT.format(order.estimatedDelivery())).append('\n');
        }
        if (order.exceptionReason() != null) {
            sb.append("- 异常原因: ").append(order.exceptionReason()).append('\n');
        }
        if (!order.logisticsTrail().isEmpty()) {
            sb.append("- 物流轨迹:\n");
            String trail = order.logisticsTrail().stream()
                    .sorted(Comparator.comparing(LogisticsEvent::time))
                    .map(e -> "  * " + TIME_FMT.format(e.time()) + " [" + e.location() + "] " + e.description())
                    .collect(Collectors.joining("\n"));
            sb.append(trail).append('\n');
        }
    }
}
