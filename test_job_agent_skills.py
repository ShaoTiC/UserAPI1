import unittest

from job_agent_skills import (
    GreetingWriterSkill,
    JobFilterSkill,
    JobPosting,
    JobSearchAgentSkills,
    Tone,
    WorkMode,
    build_default_undergraduate_profile,
)


class JobAgentSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = build_default_undergraduate_profile(
            name="李明",
            school="示例大学",
            contact="liming@example.com",
        )

    def test_filter_ranks_agent_internship_above_unrelated_job(self) -> None:
        jobs = [
            {
                "title": "Agent 开发实习生",
                "company": "Future AI",
                "description": "参与 LLM Agent、RAG、工具调用和工作流平台建设。",
                "location": "上海",
                "work_mode": "hybrid",
                "skills": "Python, FastAPI, LangChain, RAG",
                "min_days_per_week": 3,
            },
            {
                "title": "销售运营",
                "company": "Retail Co",
                "description": "负责门店活动执行和数据整理。",
                "location": "广州",
                "work_mode": "onsite",
                "skills": "Excel",
                "min_days_per_week": 5,
                "is_internship": True,
            },
        ]

        matches = JobFilterSkill(self.profile).rank(jobs)

        self.assertEqual(matches[0].job.company, "Future AI")
        self.assertGreaterEqual(matches[0].score, 65)
        self.assertTrue(matches[0].is_recommended)
        self.assertIn("Python", matches[0].matched_skills)
        self.assertLess(matches[1].score, 65)

    def test_greeting_mentions_candidate_job_and_recruiter(self) -> None:
        job = JobPosting(
            title="LLM 应用开发实习生",
            company="Agent Lab",
            description="负责 RAG 与 Agent workflow 开发。",
            location="北京",
            work_mode=WorkMode.HYBRID,
            required_skills=("Python", "RAG"),
            recruiter_name="王老师",
        )
        match = JobFilterSkill(self.profile).score(job)

        draft = GreetingWriterSkill(self.profile).draft(match, tone=Tone.FRIENDLY)

        self.assertIn("王老师您好", draft.message)
        self.assertIn("李明", draft.message)
        self.assertIn("Agent Lab", draft.message)
        self.assertIn("LLM 应用开发实习生", draft.message)
        self.assertLessEqual(len(draft.message), 260)

    def test_facade_generates_greetings_only_for_recommended_jobs(self) -> None:
        jobs = [
            {
                "title": "AI Agent Intern",
                "company": "Builder AI",
                "description": "Build tool use agents with Python and LangChain.",
                "location": "远程",
                "work_mode": "remote",
                "skills": ["Python", "LangChain"],
                "min_days_per_week": 3,
            },
            {
                "title": "行政助理",
                "company": "Office Co",
                "description": "整理资料和会议安排。",
                "location": "天津",
                "work_mode": "onsite",
                "skills": ["Office"],
                "min_days_per_week": 5,
            },
        ]

        drafts = JobSearchAgentSkills(self.profile).recommend_and_greet(jobs)

        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].job.company, "Builder AI")


if __name__ == "__main__":
    unittest.main()
