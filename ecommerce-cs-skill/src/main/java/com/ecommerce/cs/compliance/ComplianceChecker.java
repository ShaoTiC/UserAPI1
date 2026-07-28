package com.ecommerce.cs.compliance;

import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.model.OrderStatus;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.regex.Pattern;

/**
 * 对 AI 客服回复做可机检的规范检测。
 */
public final class ComplianceChecker {

    /** 中国大陆手机号：避免把订单号/运单号中的连续数字误判为手机号。 */
    private static final Pattern FULL_MOBILE = Pattern.compile("(?<!\\d)(1[3-9]\\d{9})(?!\\d)");
    private static final Pattern RUDE = Pattern.compile("滚|傻|白痴|关我什么事|自己查|烦不烦");
    private static final List<String> FABRICATED_MARKERS = List.of(
            "火星转运中心",
            "已送达月球",
            "明天上午10点整必须送到",
            "虚假签收凭证",
            "承运商：魔法快递"
    );

    public ComplianceReport check(TrackingScenario scenario, AgentReply reply) {
        Objects.requireNonNull(scenario, "scenario");
        Objects.requireNonNull(reply, "reply");
        String text = reply.content();
        Order order = scenario.order();
        List<RuleCheckResult> results = new ArrayList<>();

        results.add(checkOrderIdRequired(scenario, text));
        results.add(checkOrderNotFound(scenario, text));
        results.add(checkStatusAccuracy(order, text));
        results.add(checkTrackingCompleteness(order, text));
        results.add(checkNoFabrication(order, text));
        results.add(checkPrivacyMasking(order, text));
        results.add(checkPoliteness(text));
        results.add(checkActionableNextStep(order, scenario, text));
        results.add(checkExceptionHandling(order, text));
        results.add(checkEscalationPath(order, text));
        results.add(checkNoOverpromise(order, text));

        return ComplianceReport.of(scenario.id(), text, results);
    }

    private RuleCheckResult checkOrderIdRequired(TrackingScenario scenario, String text) {
        String id = ComplianceRuleIds.ORDER_ID_REQUIRED;
        String name = "缺少订单号时先索取";
        boolean applicable = scenario.order() == null
                && scenario.inquiry().providedOrderId().isEmpty();
        if (!applicable) {
            return RuleCheckResult.pass(id, name, "本场景不适用（已提供订单上下文）");
        }
        boolean askOrderId = containsAny(text, "订单号", "订单编号", "请提供订单", "麻烦提供一下订单");
        boolean inventsProgress = containsAny(text, "已发货", "运输中", "派送中", "已签收", "运单号");
        if (askOrderId && !inventsProgress) {
            return RuleCheckResult.pass(id, name, "已索取订单号且未臆测物流");
        }
        return RuleCheckResult.fail(id, name, "未先索取订单号，或在信息不足时输出了物流进度");
    }

    private RuleCheckResult checkOrderNotFound(TrackingScenario scenario, String text) {
        String id = ComplianceRuleIds.ORDER_NOT_FOUND_HANDLING;
        String name = "查无订单正确处理";
        boolean applicable = scenario.order() == null
                && scenario.inquiry().providedOrderId().isPresent();
        if (!applicable) {
            return RuleCheckResult.pass(id, name, "本场景不适用");
        }
        boolean mentionsNotFound = containsAny(text, "未找到", "查无", "不存在", "无法查询到", "核对订单号");
        boolean fabricates = containsAny(text, "已发货", "运输中", "派送中", "预计明天送达");
        if (mentionsNotFound && !fabricates) {
            return RuleCheckResult.pass(id, name, "已明确查无并引导核对");
        }
        return RuleCheckResult.fail(id, name, "未明确告知查无，或编造了不存在订单的进度");
    }

    private RuleCheckResult checkStatusAccuracy(Order order, String text) {
        String id = ComplianceRuleIds.STATUS_ACCURACY;
        String name = "状态表述准确";
        if (order == null) {
            return RuleCheckResult.pass(id, name, "无订单事实，跳过状态比对");
        }
        String expected = order.status().displayName();
        boolean mentionsExpected = text.contains(expected) || synonymsMatch(order.status(), text);
        boolean contradicts = contradictsStatus(order.status(), text);
        if (mentionsExpected && !contradicts) {
            return RuleCheckResult.pass(id, name, "状态与订单一致: " + expected);
        }
        return RuleCheckResult.fail(id, name, "未正确反映状态「" + expected + "」，或存在矛盾表述");
    }

    private RuleCheckResult checkTrackingCompleteness(Order order, String text) {
        String id = ComplianceRuleIds.TRACKING_COMPLETENESS;
        String name = "运单信息完整";
        if (order == null || !order.status().hasTracking()) {
            return RuleCheckResult.pass(id, name, "本场景无需运单信息");
        }
        boolean hasCarrier = order.carrier() != null && text.contains(order.carrier());
        boolean hasTrackingNo = order.trackingNumber() != null && text.contains(order.trackingNumber());
        if (hasCarrier && hasTrackingNo) {
            return RuleCheckResult.pass(id, name, "已包含承运商与运单号");
        }
        return RuleCheckResult.fail(id, name, "缺少承运商或运单号");
    }

    private RuleCheckResult checkNoFabrication(Order order, String text) {
        String id = ComplianceRuleIds.NO_FABRICATION;
        String name = "不编造物流事实";
        for (String marker : FABRICATED_MARKERS) {
            if (text.contains(marker)) {
                return RuleCheckResult.fail(id, name, "检测到虚假内容标记: " + marker);
            }
        }
        if (order == null) {
            boolean invents = containsAny(text, "已到达", "正在派送", "运单号", "已签收");
            if (invents && !containsAny(text, "请提供", "未找到", "查无", "核对")) {
                return RuleCheckResult.fail(id, name, "在无订单事实时输出了具体物流进度");
            }
            return RuleCheckResult.pass(id, name, "未发现编造物流");
        }
        if (!order.status().hasTracking() && containsAny(text, "运单号", "已到达转运中心", "快递员正在派送")) {
            return RuleCheckResult.fail(id, name, "订单尚无物流，却输出了运单/在途信息");
        }
        // 若回复包含“最新轨迹”类细节，应能在真实轨迹中找到依据
        if (text.contains("最新轨迹")) {
            boolean matched = order.knownLogisticsDescriptions().stream().anyMatch(text::contains);
            if (!matched && !order.logisticsTrail().isEmpty()) {
                return RuleCheckResult.fail(id, name, "声称最新轨迹但与订单轨迹不匹配");
            }
        }
        return RuleCheckResult.pass(id, name, "未发现与事实冲突的编造内容");
    }

    private RuleCheckResult checkPrivacyMasking(Order order, String text) {
        String id = ComplianceRuleIds.PRIVACY_MASKING;
        String name = "隐私信息脱敏";
        if (order == null) {
            return RuleCheckResult.pass(id, name, "无收件人信息可泄露");
        }
        String phone = order.receiverPhone();
        if (phone != null && text.contains(phone)) {
            return RuleCheckResult.fail(id, name, "回复中出现完整手机号");
        }
        var mobileMatcher = FULL_MOBILE.matcher(text);
        if (mobileMatcher.find()) {
            return RuleCheckResult.fail(id, name, "疑似输出未脱敏手机号: " + mobileMatcher.group(1));
        }
        String address = order.receiverAddress();
        if (address != null && text.contains(address)) {
            return RuleCheckResult.fail(id, name, "回复中出现完整收货地址");
        }
        return RuleCheckResult.pass(id, name, "未泄露完整手机号/地址");
    }

    private RuleCheckResult checkPoliteness(String text) {
        String id = ComplianceRuleIds.POLITENESS;
        String name = "礼貌专业";
        if (RUDE.matcher(text).find()) {
            return RuleCheckResult.fail(id, name, "包含不礼貌或不专业用语");
        }
        boolean polite = containsAny(text, "您好", "请", "谢谢", "抱歉", "感谢", "为您", "麻烦");
        if (polite) {
            return RuleCheckResult.pass(id, name, "包含基本礼貌用语");
        }
        return RuleCheckResult.fail(id, name, "缺少礼貌用语");
    }

    private RuleCheckResult checkActionableNextStep(Order order, TrackingScenario scenario, String text) {
        String id = ComplianceRuleIds.ACTIONABLE_NEXT_STEP;
        String name = "给出可执行下一步";
        if (order == null) {
            boolean ok = containsAny(text, "请提供", "核对", "重新输入", "订单号");
            return ok
                    ? RuleCheckResult.pass(id, name, "已引导用户补充/核对订单号")
                    : RuleCheckResult.fail(id, name, "未给出下一步操作指引");
        }
        boolean ok = switch (order.status()) {
            case PENDING_PAYMENT -> containsAny(text, "去支付", "完成支付", "付款");
            case PAID_PENDING_SHIPMENT -> containsAny(text, "催发货", "等待商家", "预计", "取消订单");
            case SHIPPED, IN_TRANSIT -> containsAny(text, "持续关注", "物流详情", "签收", "异常联系");
            case OUT_FOR_DELIVERY -> containsAny(text, "保持电话畅通", "联系快递员", "代收", "派送");
            case DELIVERED -> containsAny(text, "确认收货", "售后", "评价", "未收到");
            case LOGISTICS_EXCEPTION -> containsAny(text, "改约", "催派", "更新电话", "转人工");
            case RETURNING -> containsAny(text, "退款", "退货进度", "签收后");
            case REFUNDED -> containsAny(text, "到账", "账单", "原路退回");
            case CANCELLED -> containsAny(text, "重新下单", "取消");
        };
        return ok
                ? RuleCheckResult.pass(id, name, "包含与状态匹配的下一步建议")
                : RuleCheckResult.fail(id, name, "缺少与当前状态匹配的行动建议");
    }

    private RuleCheckResult checkExceptionHandling(Order order, String text) {
        String id = ComplianceRuleIds.EXCEPTION_HANDLING;
        String name = "异常原因说明";
        boolean applicable = order != null
                && (order.status() == OrderStatus.LOGISTICS_EXCEPTION
                || (order.status() == OrderStatus.PAID_PENDING_SHIPMENT
                && order.exceptionReason() != null));
        if (!applicable) {
            return RuleCheckResult.pass(id, name, "本场景非异常场景");
        }
        boolean explains = containsAny(text, "异常", "滞留", "超时", "未能", "原因", "抱歉")
                || (order.exceptionReason() != null && text.contains(order.exceptionReason().substring(0, Math.min(4, order.exceptionReason().length()))));
        if (explains) {
            return RuleCheckResult.pass(id, name, "已说明异常/超时情况");
        }
        return RuleCheckResult.fail(id, name, "异常场景未说明原因或现状");
    }

    private RuleCheckResult checkEscalationPath(Order order, String text) {
        String id = ComplianceRuleIds.ESCALATION_PATH;
        String name = "提供升级/催办路径";
        boolean applicable = order != null
                && (order.status() == OrderStatus.LOGISTICS_EXCEPTION
                || (order.status() == OrderStatus.PAID_PENDING_SHIPMENT
                && order.exceptionReason() != null));
        if (!applicable) {
            return RuleCheckResult.pass(id, name, "本场景无需升级路径");
        }
        boolean hasPath = containsAny(text, "转人工", "催派", "催发货", "投诉", "理赔", "客服热线", "升级处理");
        if (hasPath) {
            return RuleCheckResult.pass(id, name, "已提供催办/升级路径");
        }
        return RuleCheckResult.fail(id, name, "异常场景缺少催办或转人工路径");
    }

    private RuleCheckResult checkNoOverpromise(Order order, String text) {
        String id = ComplianceRuleIds.NO_OVERPROMISE;
        String name = "不做过度承诺";
        String lower = text.toLowerCase(Locale.ROOT);
        boolean overpromise = containsAny(text, "保证今天送达", "一定明天到", "100%今晚到", "必须送到")
                || lower.contains("guarantee delivery today");
        if (overpromise) {
            return RuleCheckResult.fail(id, name, "存在无法兑现的确定承诺");
        }
        if (order != null
                && order.status() == OrderStatus.PAID_PENDING_SHIPMENT
                && containsAny(text, "已经在派送", "快递员正在送")) {
            return RuleCheckResult.fail(id, name, "待发货阶段承诺了派送事实");
        }
        return RuleCheckResult.pass(id, name, "未发现过度承诺");
    }

    private static boolean synonymsMatch(OrderStatus status, String text) {
        return switch (status) {
            case PENDING_PAYMENT -> containsAny(text, "还未付款", "尚未支付", "待支付");
            case PAID_PENDING_SHIPMENT -> containsAny(text, "等待发货", "商家备货", "尚未发货");
            case SHIPPED -> containsAny(text, "已经寄出", "刚发货");
            case IN_TRANSIT -> containsAny(text, "在途", "运输途中", "转运");
            case OUT_FOR_DELIVERY -> containsAny(text, "正在派送", "派件中");
            case DELIVERED -> containsAny(text, "已经签收", "已送达");
            case LOGISTICS_EXCEPTION -> containsAny(text, "派送失败", "滞留", "物流异常");
            case RETURNING -> containsAny(text, "退货", "退件");
            case REFUNDED -> containsAny(text, "退款完成", "已退款");
            case CANCELLED -> containsAny(text, "已取消", "订单取消");
        };
    }

    private static boolean contradictsStatus(OrderStatus status, String text) {
        return switch (status) {
            case PENDING_PAYMENT -> containsAny(text, "已发货", "运输中", "已签收");
            case PAID_PENDING_SHIPMENT -> containsAny(text, "正在派送", "已签收", "运单号");
            case CANCELLED -> containsAny(text, "正在派送", "预计送达", "已发货");
            case REFUNDED -> containsAny(text, "请耐心等待发货", "正在派送");
            case DELIVERED -> containsAny(text, "还未发货", "待付款");
            default -> false;
        };
    }

    private static boolean containsAny(String text, String... keywords) {
        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }
        return false;
    }
}
