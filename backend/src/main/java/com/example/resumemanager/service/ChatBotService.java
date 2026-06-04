package com.example.resumemanager.service;

import com.example.resumemanager.dto.PageResult;
import com.example.resumemanager.mapper.ChatBotMapper;
import com.example.resumemanager.model.ChatBot;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class ChatBotService {
    private final ChatBotMapper chatBotMapper;

    public ChatBotService(ChatBotMapper chatBotMapper) {
        this.chatBotMapper = chatBotMapper;
    }

    public PageResult<ChatBot> findPage(String keyword, int page, int size) {
        int normalizedPage = Math.max(page, 1);
        int normalizedSize = Math.min(Math.max(size, 1), 100);
        int offset = (normalizedPage - 1) * normalizedSize;
        return new PageResult<>(
                chatBotMapper.findPage(keyword, offset, normalizedSize),
                chatBotMapper.count(keyword),
                normalizedPage,
                normalizedSize
        );
    }

    public ChatBot findById(Long id) {
        ChatBot chatBot = chatBotMapper.findById(id);
        if (chatBot == null) {
            throw new ResponseStatusException(NOT_FOUND, "微信聊天机器人不存在");
        }
        return chatBot;
    }

    public ChatBot create(ChatBot chatBot) {
        if (chatBot.getCreatedAt() == null) {
            chatBot.setCreatedAt(LocalDateTime.now());
        }
        if (chatBot.getStatus() == null || chatBot.getStatus().isBlank()) {
            chatBot.setStatus("active");
        }
        chatBotMapper.insert(chatBot);
        return findById(chatBot.getId());
    }

    public ChatBot updateStatus(Long id, String status) {
        if (chatBotMapper.updateStatus(id, status) == 0) {
            throw new ResponseStatusException(NOT_FOUND, "微信聊天机器人不存在");
        }
        return findById(id);
    }
}
