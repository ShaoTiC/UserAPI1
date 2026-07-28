package com.ecommerce.cs.skill;

import com.ecommerce.cs.compliance.ComplianceChecker;
import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.scenario.ScenarioCatalog;
import com.ecommerce.cs.scenario.TrackingScenario;
import com.ecommerce.cs.service.CompliantCustomerServiceAgent;
import com.ecommerce.cs.service.NonCompliantReplyFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * 电商订单进度 AI 客服 Skill 门面：
 * <ul>
 *   <li>按场景模拟合规客服回复</li>
 *   <li>对任意回复做规范检测</li>
 *   <li>批量跑场景回归，输出合规报告</li>
 * </ul>
 */
public final class EcommerceOrderTrackingSkill {

    private final ScenarioCatalog catalog;
    private final CompliantCustomerServiceAgent agent;
    private final NonCompliantReplyFactory nonCompliantReplyFactory;
    private final ComplianceChecker checker;

    public EcommerceOrderTrackingSkill() {
        this(new ScenarioCatalog(), new CompliantCustomerServiceAgent(),
                new NonCompliantReplyFactory(), new ComplianceChecker());
    }

    public EcommerceOrderTrackingSkill(
            ScenarioCatalog catalog,
            CompliantCustomerServiceAgent agent,
            NonCompliantReplyFactory nonCompliantReplyFactory,
            ComplianceChecker checker) {
        this.catalog = Objects.requireNonNull(catalog);
        this.agent = Objects.requireNonNull(agent);
        this.nonCompliantReplyFactory = Objects.requireNonNull(nonCompliantReplyFactory);
        this.checker = Objects.requireNonNull(checker);
        catalog.all().stream()
                .map(TrackingScenario::order)
                .filter(Objects::nonNull)
                .forEach(agent::register);
    }

    public ScenarioCatalog catalog() {
        return catalog;
    }

    public AgentReply simulateCompliantReply(String scenarioId) {
        TrackingScenario scenario = catalog.require(scenarioId);
        return agent.reply(scenario);
    }

    public AgentReply simulateNonCompliantReply(String scenarioId) {
        TrackingScenario scenario = catalog.require(scenarioId);
        return nonCompliantReplyFactory.forScenario(scenario);
    }

    public ComplianceReport evaluate(String scenarioId, String replyText) {
        TrackingScenario scenario = catalog.require(scenarioId);
        return checker.check(scenario, new AgentReply(replyText, AgentReply.ReplySource.EXTERNAL));
    }

    public ComplianceReport evaluate(TrackingScenario scenario, AgentReply reply) {
        return checker.check(scenario, reply);
    }

    public List<ComplianceReport> runCompliantRegression() {
        List<ComplianceReport> reports = new ArrayList<>();
        for (TrackingScenario scenario : catalog.all()) {
            AgentReply reply = agent.reply(scenario);
            reports.add(checker.check(scenario, reply));
        }
        return reports;
    }

    public List<ComplianceReport> runNonCompliantDetection() {
        List<ComplianceReport> reports = new ArrayList<>();
        for (TrackingScenario scenario : catalog.all()) {
            AgentReply reply = nonCompliantReplyFactory.forScenario(scenario);
            reports.add(checker.check(scenario, reply));
        }
        return reports;
    }

    public Optional<TrackingScenario> findScenario(String id) {
        return catalog.find(id);
    }

    public CompliantCustomerServiceAgent agent() {
        return agent;
    }

    public void registerOrder(Order order) {
        agent.register(order);
    }
}
