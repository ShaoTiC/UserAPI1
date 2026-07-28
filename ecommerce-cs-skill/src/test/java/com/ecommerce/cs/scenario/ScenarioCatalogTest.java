package com.ecommerce.cs.scenario;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ScenarioCatalogTest {

    @Test
    void containsExpectedScenarios() {
        ScenarioCatalog catalog = new ScenarioCatalog();
        assertEquals(12, catalog.all().size());
        assertTrue(catalog.find("S01_IN_TRANSIT").isPresent());
        assertTrue(catalog.find("S12_DELAYED_SHIPMENT").isPresent());
    }
}
