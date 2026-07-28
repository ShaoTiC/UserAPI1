package com.ecommerce.cs.llm;

import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.util.Objects;

/**
 * 单次「LLM 回复 + 规范质检」结果。
 */
public final class LlmInspectionResult {

    private final TrackingScenario scenario;
    private final AgentReply reply;
    private final ComplianceReport report;
    private final String modelName;

    public LlmInspectionResult(
            TrackingScenario scenario,
            AgentReply reply,
            ComplianceReport report,
            String modelName) {
        this.scenario = Objects.requireNonNull(scenario);
        this.reply = Objects.requireNonNull(reply);
        this.report = Objects.requireNonNull(report);
        this.modelName = Objects.requireNonNull(modelName);
    }

    public TrackingScenario scenario() {
        return scenario;
    }

    public AgentReply reply() {
        return reply;
    }

    public ComplianceReport report() {
        return report;
    }

    public String modelName() {
        return modelName;
    }

    public boolean passed() {
        return report.allPassed();
    }

    public String render() {
        StringBuilder sb = new StringBuilder();
        sb.append("模型=").append(modelName)
                .append(" | 场景=").append(scenario.id())
                .append(" | 质检=").append(passed() ? "通过" : "未通过")
                .append('\n');
        sb.append("用户: ").append(scenario.inquiry().message()).append('\n');
        sb.append("客服: ").append(reply.content()).append('\n');
        sb.append(report.render());
        return sb.toString();
    }
}
