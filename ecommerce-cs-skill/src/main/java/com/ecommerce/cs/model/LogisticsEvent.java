package com.ecommerce.cs.model;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * 单条物流轨迹节点。
 */
public final class LogisticsEvent {
    private final LocalDateTime time;
    private final String location;
    private final String description;

    public LogisticsEvent(LocalDateTime time, String location, String description) {
        this.time = Objects.requireNonNull(time, "time");
        this.location = Objects.requireNonNull(location, "location");
        this.description = Objects.requireNonNull(description, "description");
    }

    public LocalDateTime time() {
        return time;
    }

    public String location() {
        return location;
    }

    public String description() {
        return description;
    }

    @Override
    public String toString() {
        return time + " [" + location + "] " + description;
    }
}
