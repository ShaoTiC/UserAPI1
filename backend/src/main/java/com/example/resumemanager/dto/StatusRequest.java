package com.example.resumemanager.dto;

import jakarta.validation.constraints.NotBlank;

public record StatusRequest(@NotBlank String status) {
}
