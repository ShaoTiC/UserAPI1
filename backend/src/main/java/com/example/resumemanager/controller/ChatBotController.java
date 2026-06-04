package com.example.resumemanager.controller;

import com.example.resumemanager.dto.ApiResponse;
import com.example.resumemanager.dto.PageResult;
import com.example.resumemanager.dto.StatusRequest;
import com.example.resumemanager.model.ChatBot;
import com.example.resumemanager.service.ChatBotService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chatbots")
public class ChatBotController {
    private final ChatBotService chatBotService;

    public ChatBotController(ChatBotService chatBotService) {
        this.chatBotService = chatBotService;
    }

    @GetMapping
    public ApiResponse<PageResult<ChatBot>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "12") int size
    ) {
        return ApiResponse.ok(chatBotService.findPage(keyword, page, size));
    }

    @GetMapping("/{id}")
    public ApiResponse<ChatBot> detail(@PathVariable Long id) {
        return ApiResponse.ok(chatBotService.findById(id));
    }

    @PostMapping
    public ApiResponse<ChatBot> create(@RequestBody ChatBot chatBot) {
        return ApiResponse.ok("创建成功", chatBotService.create(chatBot));
    }

    @PatchMapping("/{id}/status")
    public ApiResponse<ChatBot> updateStatus(@PathVariable Long id, @Valid @RequestBody StatusRequest request) {
        return ApiResponse.ok("状态已更新", chatBotService.updateStatus(id, request.status()));
    }
}
