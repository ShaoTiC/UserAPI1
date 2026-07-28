package com.ecommerce.cs.skill;

import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.compliance.ComplianceRuleIds;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.TrackingScenario;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.List;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class EcommerceOrderTrackingSkillTest {

    private EcommerceOrderTrackingSkill skill;

    @BeforeEach
    void setUp() {
        skill = new EcommerceOrderTrackingSkill();
    }

    static Stream<String> allScenarioIds() {
        return new EcommerceOrderTrackingSkill().catalog().all().stream().map(TrackingScenario::id);
    }

    @ParameterizedTest(name = "合规模拟应通过全部规范: {0}")
    @MethodSource("allScenarioIds")
    void compliantSimulatorPassesAllRules(String scenarioId) {
        AgentReply reply = skill.simulateCompliantReply(scenarioId);
        TrackingScenario scenario = skill.catalog().require(scenarioId);
        ComplianceReport report = skill.evaluate(scenario, reply);
        assertTrue(report.allPassed(), () -> "场景 " + scenarioId + " 合规模拟未通过:\n" + report.render()
                + "\n回复: " + reply.content());
        for (String required : scenario.requiredRuleIds()) {
            assertTrue(report.passed(required),
                    () -> "场景 " + scenarioId + " 缺少必需规范 " + required + "\n" + report.render());
        }
    }

    @ParameterizedTest(name = "违规样例应被检出: {0}")
    @MethodSource("allScenarioIds")
    void nonCompliantSamplesAreDetected(String scenarioId) {
        AgentReply reply = skill.simulateNonCompliantReply(scenarioId);
        TrackingScenario scenario = skill.catalog().require(scenarioId);
        ComplianceReport report = skill.evaluate(scenario, reply);
        assertFalse(report.allPassed(),
                () -> "场景 " + scenarioId + " 的违规样例未被检出:\n" + report.render()
                        + "\n回复: " + reply.content());
        boolean hitCritical = scenario.criticalRuleIds().stream().anyMatch(report::failed);
        assertTrue(hitCritical || !report.failures().isEmpty(),
                () -> "场景 " + scenarioId + " 应至少命中一条关键或失败规范");
    }

    @Test
    @DisplayName("外部回复：运输中缺少运单号应失败")
    void externalReplyMissingTrackingFails() {
        String reply = "您好，订单 TB20260728001 运输中，请耐心等待。";
        ComplianceReport report = skill.evaluate("S01_IN_TRANSIT", reply);
        assertTrue(report.failed(ComplianceRuleIds.TRACKING_COMPLETENESS));
    }

    @Test
    @DisplayName("外部回复：泄露完整手机号应失败")
    void externalReplyPrivacyLeakFails() {
        String reply = "您好，订单运输中，承运商顺丰速运，运单号 SF1234567890。"
                + "收件人电话 13812345678，请保持畅通。";
        ComplianceReport report = skill.evaluate("S01_IN_TRANSIT", reply);
        assertTrue(report.failed(ComplianceRuleIds.PRIVACY_MASKING));
    }

    @Test
    @DisplayName("批量回归：合规模拟全部通过，违规样例全部检出")
    void batchRegression() {
        List<ComplianceReport> ok = skill.runCompliantRegression();
        assertTrue(ok.stream().allMatch(ComplianceReport::allPassed));

        List<ComplianceReport> bad = skill.runNonCompliantDetection();
        assertTrue(bad.stream().noneMatch(ComplianceReport::allPassed));
    }
}
