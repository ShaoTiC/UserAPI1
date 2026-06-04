package com.example.resumemanager.mapper;

import com.example.resumemanager.dto.ResumeQuery;
import com.example.resumemanager.dto.StatItem;
import com.example.resumemanager.model.Resume;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ResumeMapper {
    List<Resume> findPage(@Param("query") ResumeQuery query);

    long count(@Param("query") ResumeQuery query);

    Resume findById(Long id);

    List<StatItem> countByStatus();

    int insert(Resume resume);

    int update(Resume resume);

    int updateStatus(@Param("id") Long id, @Param("status") String status);

    int deleteById(Long id);
}
