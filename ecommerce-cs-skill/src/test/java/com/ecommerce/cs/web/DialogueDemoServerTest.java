package com.ecommerce.cs.web;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DialogueDemoServerTest {

    @Test
    void parsesFlatJsonBody() {
        Map<String, String> map = DialogueDemoServer.parseJsonObject(
                "{\"scenarioId\":\"S01_IN_TRANSIT\",\"nonCompliant\":false}");
        assertEquals("S01_IN_TRANSIT", map.get("scenarioId"));
        assertEquals("false", map.get("nonCompliant"));
    }
}
