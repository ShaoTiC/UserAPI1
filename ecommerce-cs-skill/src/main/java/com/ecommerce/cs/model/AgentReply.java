package com.ecommerce.cs.model;

import java.util.Objects;

/**
 * AI 客服的一条回复（可来自规范模拟器，也可来自待检测的外部文本）。
 */
public final class AgentReply {
    private final String content;
    private final ReplySource source;

    public enum ReplySource {
        /** 本 skill 内置的合规模拟客服 */
        COMPLIANT_SIMULATOR,
        /** 故意生成的违规样例，用于检测器回归 */
        NON_COMPLIANT_SAMPLE,
        /** 外部/待测回复 */
        EXTERNAL
    }

    public AgentReply(String content, ReplySource source) {
        this.content = Objects.requireNonNull(content, "content");
        this.source = Objects.requireNonNull(source, "source");
    }

    public String content() {
        return content;
    }

    public ReplySource source() {
        return source;
    }
}
