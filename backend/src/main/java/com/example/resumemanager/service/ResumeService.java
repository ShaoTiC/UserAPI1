package com.example.resumemanager.service;

import com.example.resumemanager.dto.PageResult;
import com.example.resumemanager.dto.ResumeQuery;
import com.example.resumemanager.dto.StatItem;
import com.example.resumemanager.mapper.ResumeMapper;
import com.example.resumemanager.model.Resume;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class ResumeService {
    private static final Map<String, String> STATUS_LABELS = new LinkedHashMap<>();

    static {
        STATUS_LABELS.put("unassigned", "未分配");
        STATUS_LABELS.put("assigned", "已分配");
        STATUS_LABELS.put("boss", "BOSS");
        STATUS_LABELS.put("phone", "手机上传");
        STATUS_LABELS.put("previous", "前程无忧");
    }

    private final ResumeMapper resumeMapper;

    public ResumeService(ResumeMapper resumeMapper) {
        this.resumeMapper = resumeMapper;
    }

    public PageResult<Resume> findPage(ResumeQuery query) {
        normalizePage(query);
        return new PageResult<>(resumeMapper.findPage(query), resumeMapper.count(query), query.getPage(), query.getSize());
    }

    public List<StatItem> stats() {
        Map<String, Long> counts = new LinkedHashMap<>();
        long total = 0;
        for (StatItem item : resumeMapper.countByStatus()) {
            counts.put(item.getKeyName(), item.getCount());
            total += item.getCount();
        }

        List<StatItem> result = new ArrayList<>();
        StatItem all = new StatItem();
        all.setKeyName("all");
        all.setLabel("全部");
        all.setCount(total);
        result.add(all);

        STATUS_LABELS.forEach((key, label) -> {
            StatItem item = new StatItem();
            item.setKeyName(key);
            item.setLabel(label);
            item.setCount(counts.getOrDefault(key, 0L));
            result.add(item);
        });
        return result;
    }

    public Resume findById(Long id) {
        Resume resume = resumeMapper.findById(id);
        if (resume == null) {
            throw new ResponseStatusException(NOT_FOUND, "简历不存在");
        }
        return resume;
    }

    public Resume create(Resume resume) {
        if (resume.getImportedAt() == null) {
            resume.setImportedAt(LocalDateTime.now());
        }
        if (resume.getStatus() == null || resume.getStatus().isBlank()) {
            resume.setStatus("unassigned");
        }
        resumeMapper.insert(resume);
        return findById(resume.getId());
    }

    public Resume update(Long id, Resume resume) {
        findById(id);
        resume.setId(id);
        resumeMapper.update(resume);
        return findById(id);
    }

    public Resume updateStatus(Long id, String status) {
        if (!STATUS_LABELS.containsKey(status)) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, "未知简历状态");
        }
        if (resumeMapper.updateStatus(id, status) == 0) {
            throw new ResponseStatusException(NOT_FOUND, "简历不存在");
        }
        return findById(id);
    }

    public void delete(Long id) {
        if (resumeMapper.deleteById(id) == 0) {
            throw new ResponseStatusException(NOT_FOUND, "简历不存在");
        }
    }

    private void normalizePage(ResumeQuery query) {
        if (query.getPage() < 1) {
            query.setPage(1);
        }
        if (query.getSize() < 1) {
            query.setSize(10);
        }
        if (query.getSize() > 100) {
            query.setSize(100);
        }
    }
}
