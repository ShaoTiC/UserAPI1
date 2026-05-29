# Job Search Agent Skills

Python skills for a CS undergraduate looking for an agent-development
internship.  The module can:

- filter and rank internship postings by Agent/LLM relevance, skills, location,
  work mode, and schedule fit;
- generate short personalized recruiter greetings for recommended postings;
- return explainable scores, matched skills, matched keywords, reasons, and
  risks.

## Quick start

```bash
python job_agent_skills.py
python -m unittest
```

## Example

```python
from job_agent_skills import JobSearchAgentSkills, build_default_undergraduate_profile

profile = build_default_undergraduate_profile(
    name="李明",
    school="示例大学",
    contact="liming@example.com",
)

jobs = [
    {
        "title": "Agent 开发实习生",
        "company": "Future AI",
        "description": "参与 LLM Agent、RAG、工具调用和工作流平台建设。",
        "location": "上海",
        "work_mode": "hybrid",
        "skills": "Python, FastAPI, LangChain, RAG",
        "min_days_per_week": 3,
        "recruiter_name": "王老师",
    }
]

agent_skills = JobSearchAgentSkills(profile)
for draft in agent_skills.recommend_and_greet(jobs):
    print(draft.message)
```
