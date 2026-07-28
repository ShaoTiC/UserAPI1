package com.ecommerce.cs.llm;

import com.ecommerce.cs.compliance.ComplianceChecker;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.ScenarioCatalog;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class LlmQualityInspectionServiceTest {

    @Test
    void fakeLlmReplyIsInspected() {
        ScenarioCatalog catalog = new ScenarioCatalog();
        LlmClient fake = new LlmClient() {
            @Override
            public String chat(String systemPrompt, String userPrompt) {
                return "您好，已为您查询到订单 TB20260728001，当前状态：运输中。"
                        + "承运商：顺丰速运，运单号：SF1234567890。"
                        + "收件人手机：138****5678；收货地址：浙江省杭州市***。"
                        + "最新轨迹：快件运输中。请持续关注物流详情；签收前请当面核对。";
            }

            @Override
            public String modelName() {
                return "fake-internal-llm";
            }
        };

        LlmQualityInspectionService service = new LlmQualityInspectionService(
                catalog,
                new LlmCustomerServiceAgent(fake),
                new ComplianceChecker());

        LlmInspectionResult result = service.inspectScenario("S01_IN_TRANSIT");
        assertEquals(AgentReply.ReplySource.LLM, result.reply().source());
        assertTrue(result.passed(), () -> result.render());
        assertEquals("fake-internal-llm", result.modelName());
    }
}
