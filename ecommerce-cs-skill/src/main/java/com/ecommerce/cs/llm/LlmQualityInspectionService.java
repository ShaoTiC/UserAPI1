package com.ecommerce.cs.llm;

import com.ecommerce.cs.compliance.ComplianceChecker;
import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.ScenarioCatalog;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * LLM 生成回复后立刻做规范质检的流水线。
 */
public final class LlmQualityInspectionService {

    private final ScenarioCatalog catalog;
    private final LlmCustomerServiceAgent llmAgent;
    private final ComplianceChecker checker;

    public LlmQualityInspectionService(
            ScenarioCatalog catalog,
            LlmCustomerServiceAgent llmAgent,
            ComplianceChecker checker) {
        this.catalog = Objects.requireNonNull(catalog);
        this.llmAgent = Objects.requireNonNull(llmAgent);
        this.checker = Objects.requireNonNull(checker);
    }

    public static LlmQualityInspectionService fromEnv(ScenarioCatalog catalog) {
        LlmConfig config = LlmConfig.fromEnv();
        LlmClient client = new OpenAiCompatibleLlmClient(config);
        return new LlmQualityInspectionService(
                catalog,
                new LlmCustomerServiceAgent(client),
                new ComplianceChecker());
    }

    public LlmInspectionResult inspectScenario(String scenarioId) {
        TrackingScenario scenario = catalog.require(scenarioId);
        return inspectScenario(scenario);
    }

    public LlmInspectionResult inspectScenario(TrackingScenario scenario) {
        AgentReply reply = llmAgent.reply(scenario);
        ComplianceReport report = checker.check(scenario, reply);
        return new LlmInspectionResult(scenario, reply, report, llmAgent.modelName());
    }

    public List<LlmInspectionResult> inspectAll() {
        List<LlmInspectionResult> results = new ArrayList<>();
        for (TrackingScenario scenario : catalog.all()) {
            results.add(inspectScenario(scenario));
        }
        return results;
    }

    public LlmCustomerServiceAgent llmAgent() {
        return llmAgent;
    }
}
