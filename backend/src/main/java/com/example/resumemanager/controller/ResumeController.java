package com.example.resumemanager.controller;

import com.example.resumemanager.dto.ApiResponse;
import com.example.resumemanager.dto.PageResult;
import com.example.resumemanager.dto.ResumeQuery;
import com.example.resumemanager.dto.StatItem;
import com.example.resumemanager.dto.StatusRequest;
import com.example.resumemanager.model.Resume;
import com.example.resumemanager.service.ResumeService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/resumes")
public class ResumeController {
    private final ResumeService resumeService;

    public ResumeController(ResumeService resumeService) {
        this.resumeService = resumeService;
    }

    @GetMapping
    public ApiResponse<PageResult<Resume>> list(@ModelAttribute ResumeQuery query) {
        return ApiResponse.ok(resumeService.findPage(query));
    }

    @GetMapping("/stats")
    public ApiResponse<List<StatItem>> stats() {
        return ApiResponse.ok(resumeService.stats());
    }

    @GetMapping("/{id}")
    public ApiResponse<Resume> detail(@PathVariable Long id) {
        return ApiResponse.ok(resumeService.findById(id));
    }

    @PostMapping
    public ApiResponse<Resume> create(@RequestBody Resume resume) {
        return ApiResponse.ok("创建成功", resumeService.create(resume));
    }

    @PutMapping("/{id}")
    public ApiResponse<Resume> update(@PathVariable Long id, @RequestBody Resume resume) {
        return ApiResponse.ok("更新成功", resumeService.update(id, resume));
    }

    @PatchMapping("/{id}/status")
    public ApiResponse<Resume> updateStatus(@PathVariable Long id, @Valid @RequestBody StatusRequest request) {
        return ApiResponse.ok("状态已更新", resumeService.updateStatus(id, request.status()));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        resumeService.delete(id);
        return ApiResponse.ok("删除成功", null);
    }
}
