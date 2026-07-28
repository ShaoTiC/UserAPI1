package com.ecommerce.cs.compliance;

import java.util.Objects;

/**
 * 单条规范检测结果。
 */
public final class RuleCheckResult {
    private final String ruleId;
    private final String ruleName;
    private final boolean passed;
    private final String detail;

    public RuleCheckResult(String ruleId, String ruleName, boolean passed, String detail) {
        this.ruleId = Objects.requireNonNull(ruleId, "ruleId");
        this.ruleName = Objects.requireNonNull(ruleName, "ruleName");
        this.passed = passed;
        this.detail = Objects.requireNonNull(detail, "detail");
    }

    public String ruleId() {
        return ruleId;
    }

    public String ruleName() {
        return ruleName;
    }

    public boolean passed() {
        return passed;
    }

    public String detail() {
        return detail;
    }

    public static RuleCheckResult pass(String ruleId, String ruleName, String detail) {
        return new RuleCheckResult(ruleId, ruleName, true, detail);
    }

    public static RuleCheckResult fail(String ruleId, String ruleName, String detail) {
        return new RuleCheckResult(ruleId, ruleName, false, detail);
    }
}
