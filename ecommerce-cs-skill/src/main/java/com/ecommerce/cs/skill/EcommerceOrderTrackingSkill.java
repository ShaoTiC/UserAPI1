package com.ecommerce.cs.skill;

import com.ecommerce.cs.compliance.ComplianceChecker;
import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.llm.LlmConfig;
import com.ecommerce.cs.llm.LlmCustomerServiceAgent;
import com.ecommerce.cs.llm.LlmInspectionResult;
import com.ecommerce.cs.llm.LlmQualityInspectionService;
import com.ecommerce.cs.llm.OpenAiCompatibleLlmClient;
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
 *   <li>按场景模拟合规客服回复（规则模板）</li>
 *   <li>调用真实 LLM（OpenAI 兼容内部大模型）生成回复并质检</li>
 *   <li>对任意回复做规范检测</li>
 *   <li>批量跑场景回归，输出合规报告</li>
 * </ul>
 */
public final class EcommerceOrderTrackingSkill {

    private final ScenarioCatalog catalog;
    private final CompliantCustomerServiceAgent agent;
    private final NonCompliantReplyFactory nonCompliantReplyFactory;
    private final ComplianceChecker checker;
    private final LlmQualityInspectionService llmInspection;

    public EcommerceOrderTrackingSkill() {
        this(new ScenarioCatalog(), new CompliantCustomerServiceAgent(),
                new NonCompliantReplyFactory(), new ComplianceChecker(), null);
    }

    public EcommerceOrderTrackingSkill(
            ScenarioCatalog catalog,
            CompliantCustomerServiceAgent agent,
            NonCompliantReplyFactory nonCompliantReplyFactory,
            ComplianceChecker checker) {
        this(catalog, agent, nonCompliantReplyFactory, checker, null);
    }

    public EcommerceOrderTrackingSkill(
            ScenarioCatalog catalog,
            CompliantCustomerServiceAgent agent,
            NonCompliantReplyFactory nonCompliantReplyFactory,
            ComplianceChecker checker,
            LlmQualityInspectionService llmInspection) {
        this.catalog = Objects.requireNonNull(catalog);
        this.agent = Objects.requireNonNull(agent);
        this.nonCompliantReplyFactory = Objects.requireNonNull(nonCompliantReplyFactory);
        this.checker = Objects.requireNonNull(checker);
        this.llmInspection = llmInspection;
        catalog.all().stream()
                .map(TrackingScenario::order)
                .filter(Objects::nonNull)
                .forEach(agent::register);
    }

    /**
     * 使用环境变量中的 LLM 配置创建带真实大模型质检能力的 Skill。
     */
    public static EcommerceOrderTrackingSkill withLlmFromEnv() {
        ScenarioCatalog catalog = new ScenarioCatalog();
        LlmConfig config = LlmConfig.fromEnv();
        LlmQualityInspectionService llm = new LlmQualityInspectionService(
                catalog,
                new LlmCustomerServiceAgent(new OpenAiCompatibleLlmClient(config)),
                new ComplianceChecker());
        return new EcommerceOrderTrackingSkill(
                catalog,
                new CompliantCustomerServiceAgent(),
                new NonCompliantReplyFactory(),
                new ComplianceChecker(),
                llm);
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

    /**
     * 调用真实 LLM 生成回复，并立刻做规范质检。
     */
    public LlmInspectionResult simulateWithLlmAndInspect(String scenarioId) {
        return requireLlm().inspectScenario(scenarioId);
    }

    public List<LlmInspectionResult> runLlmInspectionRegression() {
        return requireLlm().inspectAll();
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

    public Optional<LlmQualityInspectionService> llmInspection() {
        return Optional.ofNullable(llmInspection);
    }

    public void registerOrder(Order order) {
        agent.register(order);
    }

    private LlmQualityInspectionService requireLlm() {
        if (llmInspection == null) {
            throw new IllegalStateException(
                    "未配置 LLM。请使用 EcommerceOrderTrackingSkill.withLlmFromEnv()，"
                            + "并设置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。");
        }
        return llmInspection;
    }
}
