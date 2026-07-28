package com.ecommerce.cs.service;

import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.scenario.TrackingScenario;

/**
 * 故意生成不合规回复，用于验证规范检测器能抓到问题。
 */
public final class NonCompliantReplyFactory {

    public AgentReply forScenario(TrackingScenario scenario) {
        return switch (scenario.id()) {
            case "S07_MISSING_ORDER_ID" -> new AgentReply(
                    "你的快递已经在派送了，运单号 SF000000，明天上午10点整必须送到。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S08_ORDER_NOT_FOUND" -> new AgentReply(
                    "查到了，订单 FAKE000000 运输中，刚到火星转运中心。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S01_IN_TRANSIT" -> privacyLeak(scenario.order());
            case "S02_PENDING_PAYMENT" -> new AgentReply(
                    "已经发货了，承运商：魔法快递，运单号 MAGIC001，正在派送。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S03_PENDING_SHIPMENT" -> new AgentReply(
                    "保证今天送达，快递员正在送，运单号已经有了。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S06_LOGISTICS_EXCEPTION" -> new AgentReply(
                    "在路上呢，等等就行。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S12_DELAYED_SHIPMENT" -> new AgentReply(
                    "还没发，你自己等着吧，烦不烦。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S11_CANCELLED" -> new AgentReply(
                    "正在派送，预计明天送达，请耐心等待发货。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            case "S05_DELIVERED" -> new AgentReply(
                    "还未发货，请先去支付。最新轨迹：已送达月球。",
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
            default -> new AgentReply(
                    "滚，自己查物流去。收件人电话："
                            + (scenario.order() == null ? "13812345678" : scenario.order().receiverPhone())
                            + "，地址："
                            + (scenario.order() == null ? "完整地址" : scenario.order().receiverAddress()),
                    AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
            );
        };
    }

    private AgentReply privacyLeak(Order order) {
        return new AgentReply(
                "订单在运输中。收件人电话：" + order.receiverPhone()
                        + "，地址：" + order.receiverAddress()
                        + "。承运商：随便编的，运单号也没有。",
                AgentReply.ReplySource.NON_COMPLIANT_SAMPLE
        );
    }
}
