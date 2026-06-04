package com.example.resumemanager.config;

import com.example.resumemanager.dto.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ApiResponse<Void>> handleStatusException(ResponseStatusException exception) {
        return ResponseEntity
                .status(exception.getStatusCode())
                .body(ApiResponse.fail(exception.getReason()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException exception) {
        return ResponseEntity.badRequest().body(ApiResponse.fail("请求参数不合法"));
    }
}
