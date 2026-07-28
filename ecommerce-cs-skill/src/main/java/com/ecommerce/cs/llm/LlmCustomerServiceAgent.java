package com.ecommerce.cs.llm;

import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.model.CustomerInquiry;
import com.ecommerce.cs.model.Order;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.util.Objects;
import java.util.Optional;

/**
 * 调用真实 LLM 生成客服回复。
 */
public final class LlmCustomerServiceAgent {

    private final LlmClient client;
    private final LlmPromptBuilder promptBuilder;

    public LlmCustomerServiceAgent(LlmClient client) {
        this(client, new LlmPromptBuilder());
    }

    public LlmCustomerServiceAgent(LlmClient client, LlmPromptBuilder promptBuilder) {
        this.client = Objects.requireNonNull(client, "client");
        this.promptBuilder = Objects.requireNonNull(promptBuilder, "promptBuilder");
    }

    public AgentReply reply(TrackingScenario scenario) {
        String content = client.chat(promptBuilder.systemPrompt(), promptBuilder.userPrompt(scenario));
        return new AgentReply(content, AgentReply.ReplySource.LLM);
    }

    public AgentReply reply(CustomerInquiry inquiry, Optional<Order> order) {
        String content = client.chat(
                promptBuilder.systemPrompt(),
                promptBuilder.userPrompt(inquiry, order.orElse(null)));
        return new AgentReply(content, AgentReply.ReplySource.LLM);
    }

    public String modelName() {
        return client.modelName();
    }
}
