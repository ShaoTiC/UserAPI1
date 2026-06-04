package com.example.resumemanager.mapper;

import com.example.resumemanager.model.ChatBot;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ChatBotMapper {
    List<ChatBot> findPage(@Param("keyword") String keyword, @Param("offset") int offset, @Param("size") int size);

    long count(@Param("keyword") String keyword);

    ChatBot findById(Long id);

    int insert(ChatBot chatBot);

    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
