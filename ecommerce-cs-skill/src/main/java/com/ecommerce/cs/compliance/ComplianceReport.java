package com.ecommerce.cs.compliance;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 一次回复的完整规范检测报告。
 */
public final class ComplianceReport {
    private final String scenarioId;
    private final String replyPreview;
    private final List<RuleCheckResult> results;

    public ComplianceReport(String scenarioId, String replyPreview, List<RuleCheckResult> results) {
        this.scenarioId = Objects.requireNonNull(scenarioId, "scenarioId");
        this.replyPreview = Objects.requireNonNull(replyPreview, "replyPreview");
        this.results = List.copyOf(results);
    }

    public String scenarioId() {
        return scenarioId;
    }

    public String replyPreview() {
        return replyPreview;
    }

    public List<RuleCheckResult> results() {
        return results;
    }

    public boolean allPassed() {
        return results.stream().allMatch(RuleCheckResult::passed);
    }

    public List<RuleCheckResult> failures() {
        return results.stream().filter(r -> !r.passed()).toList();
    }

    public boolean passed(String ruleId) {
        return results.stream()
                .filter(r -> r.ruleId().equals(ruleId))
                .findFirst()
                .map(RuleCheckResult::passed)
                .orElse(false);
    }

    public boolean failed(String ruleId) {
        return results.stream()
                .anyMatch(r -> r.ruleId().equals(ruleId) && !r.passed());
    }

    public String render() {
        StringBuilder sb = new StringBuilder();
        sb.append("场景=").append(scenarioId)
                .append(" | 总体=").append(allPassed() ? "合规" : "不合规")
                .append('\n');
        for (RuleCheckResult result : results) {
            sb.append("  [")
                    .append(result.passed() ? "PASS" : "FAIL")
                    .append("] ")
                    .append(result.ruleId())
                    .append(" - ")
                    .append(result.ruleName())
                    .append(": ")
                    .append(result.detail())
                    .append('\n');
        }
        if (!failures().isEmpty()) {
            sb.append("失败项: ")
                    .append(failures().stream().map(RuleCheckResult::ruleId).collect(Collectors.joining(", ")))
                    .append('\n');
        }
        return sb.toString();
    }

    public static ComplianceReport of(String scenarioId, String reply, List<RuleCheckResult> results) {
        String preview = reply.length() <= 80 ? reply : reply.substring(0, 80) + "...";
        return new ComplianceReport(scenarioId, preview, new ArrayList<>(results));
    }
}
