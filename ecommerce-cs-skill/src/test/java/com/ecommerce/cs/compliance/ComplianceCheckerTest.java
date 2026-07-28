package com.ecommerce.cs.compliance;

import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.ScenarioCatalog;
import com.ecommerce.cs.scenario.TrackingScenario;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ComplianceCheckerTest {

    private final ScenarioCatalog catalog = new ScenarioCatalog();
    private final ComplianceChecker checker = new ComplianceChecker();

    @Test
    void missingOrderIdMustAskBeforeInventingProgress() {
        TrackingScenario scenario = catalog.require("S07_MISSING_ORDER_ID");
        ComplianceReport bad = checker.check(scenario, new AgentReply(
                "已经发货了，运单号 SF1，正在派送。", AgentReply.ReplySource.EXTERNAL));
        assertTrue(bad.failed(ComplianceRuleIds.ORDER_ID_REQUIRED));
        assertTrue(bad.failed(ComplianceRuleIds.NO_FABRICATION));

        ComplianceReport good = checker.check(scenario, new AgentReply(
                "您好，请提供订单号，我再帮您查询进度。", AgentReply.ReplySource.EXTERNAL));
        assertTrue(good.passed(ComplianceRuleIds.ORDER_ID_REQUIRED));
        assertTrue(good.passed(ComplianceRuleIds.NO_FABRICATION));
    }

    @Test
    void exceptionScenarioRequiresEscalation() {
        TrackingScenario scenario = catalog.require("S06_LOGISTICS_EXCEPTION");
        ComplianceReport bad = checker.check(scenario, new AgentReply(
                "您好，订单物流异常，运单号 ZT1122334455，承运商中通快递。请再等等。",
                AgentReply.ReplySource.EXTERNAL));
        assertTrue(bad.failed(ComplianceRuleIds.ESCALATION_PATH));

        ComplianceReport good = checker.check(scenario, new AgentReply(
                "您好，订单物流异常：派送失败。承运商中通快递，运单号 ZT1122334455。"
                        + "收件手机 138****5678。建议改约派送或催派，也可转人工升级处理。",
                AgentReply.ReplySource.EXTERNAL));
        assertTrue(good.passed(ComplianceRuleIds.ESCALATION_PATH));
        assertTrue(good.passed(ComplianceRuleIds.EXCEPTION_HANDLING));
        assertTrue(good.passed(ComplianceRuleIds.PRIVACY_MASKING));
    }

    @Test
    void cancelledOrderMustNotPromiseShipment() {
        TrackingScenario scenario = catalog.require("S11_CANCELLED");
        ComplianceReport bad = checker.check(scenario, new AgentReply(
                "您好，订单已取消。正在派送，预计明天送达。", AgentReply.ReplySource.EXTERNAL));
        assertTrue(bad.failed(ComplianceRuleIds.STATUS_ACCURACY)
                || bad.failed(ComplianceRuleIds.NO_FABRICATION)
                || bad.failed(ComplianceRuleIds.NO_OVERPROMISE));
        assertFalse(bad.allPassed());
    }
}
