"""Skills for an internship-search agent.

The module is intentionally dependency-free so it can be dropped into a small
agent project and reused by either a CLI, a workflow engine, or an LLM tool
wrapper.  It focuses on two skills:

1. Filter and rank agent-development internship postings.
2. Draft personalized greeting messages for recruiters or hiring managers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class WorkMode(str, Enum):
    """Supported work-mode preferences."""

    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class Tone(str, Enum):
    """Greeting styles supported by the greeting skill."""

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONFIDENT = "confident"


@dataclass(frozen=True)
class CandidateProfile:
    """Profile of a CS undergraduate looking for agent-development internships."""

    name: str
    school: str
    major: str = "计算机科学与技术"
    target_roles: tuple[str, ...] = (
        "agent开发实习生",
        "AI agent intern",
        "LLM应用开发实习生",
        "后端开发实习生",
    )
    skills: tuple[str, ...] = (
        "Python",
        "FastAPI",
        "LangChain",
        "RAG",
        "LLM",
        "Prompt Engineering",
        "REST API",
        "SQL",
    )
    projects: tuple[str, ...] = (
        "实现过可调用工具的任务型 Agent",
        "搭建过基于 RAG 的知识库问答服务",
    )
    preferred_locations: tuple[str, ...] = ("北京", "上海", "深圳", "杭州", "远程")
    preferred_work_modes: tuple[WorkMode, ...] = (WorkMode.REMOTE, WorkMode.HYBRID)
    min_days_per_week: int = 3
    can_start: str = "尽快"
    contact: str = ""


@dataclass(frozen=True)
class JobPosting:
    """A normalized job posting consumed by the filtering skill."""

    title: str
    company: str
    description: str
    location: str = ""
    work_mode: WorkMode = WorkMode.UNKNOWN
    required_skills: tuple[str, ...] = ()
    min_days_per_week: int | None = None
    is_internship: bool = True
    url: str = ""
    recruiter_name: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "JobPosting":
        """Build a posting from common dictionary keys used by crawlers/APIs."""

        work_mode = _parse_work_mode(str(raw.get("work_mode") or raw.get("mode") or ""))
        skills = raw.get("required_skills") or raw.get("skills") or ()
        if isinstance(skills, str):
            required_skills = tuple(_split_keywords(skills))
        else:
            required_skills = tuple(str(skill).strip() for skill in skills if str(skill).strip())

        return cls(
            title=str(raw.get("title", "")).strip(),
            company=str(raw.get("company", "")).strip(),
            description=str(raw.get("description", "")).strip(),
            location=str(raw.get("location", "")).strip(),
            work_mode=work_mode,
            required_skills=required_skills,
            min_days_per_week=_parse_optional_int(raw.get("min_days_per_week")),
            is_internship=bool(raw.get("is_internship", True)),
            url=str(raw.get("url", "")).strip(),
            recruiter_name=str(raw.get("recruiter_name", "")).strip(),
        )


@dataclass(frozen=True)
class JobMatch:
    """Filtering result with explainable scoring details."""

    job: JobPosting
    score: int
    matched_skills: tuple[str, ...] = ()
    matched_keywords: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()

    @property
    def is_recommended(self) -> bool:
        """Whether the score is strong enough for an automatic greeting draft."""

        return self.score >= 65


@dataclass(frozen=True)
class GreetingDraft:
    """Greeting generated for a matched job posting."""

    job: JobPosting
    message: str
    highlights: tuple[str, ...]


class JobFilterSkill:
    """Rank internship postings for an agent-development internship search."""

    AGENT_KEYWORDS: tuple[str, ...] = (
        "agent",
        "智能体",
        "llm",
        "大模型",
        "rag",
        "function calling",
        "tool use",
        "工具调用",
        "workflow",
        "langchain",
        "llamaindex",
        "prompt",
    )

    def __init__(self, profile: CandidateProfile, threshold: int = 65) -> None:
        self.profile = profile
        self.threshold = threshold

    def rank(self, jobs: Iterable[JobPosting | Mapping[str, Any]]) -> list[JobMatch]:
        """Score jobs and return them from strongest to weakest."""

        matches = [self.score(_ensure_job(job)) for job in jobs]
        return sorted(matches, key=lambda match: match.score, reverse=True)

    def filter(self, jobs: Iterable[JobPosting | Mapping[str, Any]]) -> list[JobMatch]:
        """Return only postings that meet the configured score threshold."""

        return [match for match in self.rank(jobs) if match.score >= self.threshold]

    def score(self, job: JobPosting) -> JobMatch:
        """Compute a transparent suitability score for one posting."""

        score = 0
        reasons: list[str] = []
        risks: list[str] = []

        text = _normalize_text(" ".join([job.title, job.company, job.description]))
        target_role_hits = _keyword_hits(text, self.profile.target_roles)
        if target_role_hits:
            score += min(25, 10 + 5 * len(target_role_hits))
            reasons.append(f"岗位方向匹配：{', '.join(target_role_hits)}")

        agent_hits = _keyword_hits(text, self.AGENT_KEYWORDS)
        if agent_hits:
            score += min(25, 8 + 4 * len(agent_hits))
            reasons.append(f"包含 Agent/LLM 相关关键词：{', '.join(agent_hits)}")

        matched_skills = _skill_overlap(self.profile.skills, job.required_skills, text)
        if matched_skills:
            score += min(25, 5 + 4 * len(matched_skills))
            reasons.append(f"技能匹配：{', '.join(matched_skills)}")
        else:
            risks.append("岗位技能要求与当前简历关键词重合较少")

        if job.is_internship:
            score += 10
            reasons.append("岗位类型为实习")
        else:
            score -= 20
            risks.append("岗位不是实习岗位")

        location_score, location_reason = self._score_location(job)
        score += location_score
        if location_reason:
            reasons.append(location_reason)

        schedule_score, schedule_reason, schedule_risk = self._score_schedule(job)
        score += schedule_score
        if schedule_reason:
            reasons.append(schedule_reason)
        if schedule_risk:
            risks.append(schedule_risk)

        score = max(0, min(100, score))
        if score < self.threshold:
            risks.append(f"综合分 {score} 低于阈值 {self.threshold}")

        return JobMatch(
            job=job,
            score=score,
            matched_skills=matched_skills,
            matched_keywords=agent_hits,
            reasons=tuple(reasons),
            risks=tuple(risks),
        )

    def _score_location(self, job: JobPosting) -> tuple[int, str]:
        preferred_locations = tuple(location.lower() for location in self.profile.preferred_locations)
        job_location = job.location.lower()

        if job.work_mode in self.profile.preferred_work_modes:
            return 10, f"工作方式匹配：{job.work_mode.value}"
        if "远程" in preferred_locations and job.work_mode == WorkMode.REMOTE:
            return 10, "支持远程"
        if job_location and any(location in job_location for location in preferred_locations):
            return 8, f"地点匹配：{job.location}"
        if not job_location and job.work_mode == WorkMode.UNKNOWN:
            return 0, ""
        return -5, f"地点或工作方式可能不匹配：{job.location or job.work_mode.value}"

    def _score_schedule(self, job: JobPosting) -> tuple[int, str, str]:
        if job.min_days_per_week is None:
            return 0, "", ""
        if job.min_days_per_week <= self.profile.min_days_per_week:
            return 5, f"出勤要求可满足：每周 {job.min_days_per_week} 天"
        return -8, "", f"出勤要求偏高：每周 {job.min_days_per_week} 天"


class GreetingWriterSkill:
    """Create concise personalized recruiter greetings for matched jobs."""

    def __init__(self, profile: CandidateProfile) -> None:
        self.profile = profile

    def draft(
        self,
        match: JobMatch,
        tone: Tone = Tone.PROFESSIONAL,
        max_chars: int = 260,
    ) -> GreetingDraft:
        """Generate a greeting message from a scored job match."""

        job = match.job
        salutation = f"{job.recruiter_name}您好" if job.recruiter_name else "您好"
        highlights = self._select_highlights(match)
        project_line = self.profile.projects[0] if self.profile.projects else "有完整项目开发经验"

        tone_opener = {
            Tone.PROFESSIONAL: "我正在寻找 Agent/LLM 应用开发方向的实习机会",
            Tone.FRIENDLY: "我最近在关注 Agent/LLM 应用开发实习机会",
            Tone.CONFIDENT: "我希望申请贵司 Agent/LLM 应用开发相关实习岗位",
        }[tone]

        message = (
            f"{salutation}，我叫{self.profile.name}，是{self.profile.school}"
            f"{self.profile.major}本科生。{tone_opener}，看到{job.company}的"
            f"「{job.title}」后很感兴趣。我的匹配点包括：{_join_cn(highlights)}；"
            f"{project_line}。如果岗位仍在招聘，期待和您进一步沟通，"
            f"我可{self.profile.can_start}开始实习。"
        )

        if self.profile.contact:
            message += f"联系方式：{self.profile.contact}。"

        return GreetingDraft(
            job=job,
            message=_trim_to_sentence(message, max_chars),
            highlights=highlights,
        )

    def _select_highlights(self, match: JobMatch) -> tuple[str, ...]:
        highlights: list[str] = []
        if match.matched_skills:
            highlights.append("熟悉 " + "、".join(match.matched_skills[:3]))
        if match.matched_keywords:
            highlights.append("关注 " + "、".join(match.matched_keywords[:3]) + " 方向")
        if not highlights:
            highlights.append("具备 Python 后端和 AI 应用项目经验")
        if self.profile.min_days_per_week:
            highlights.append(f"每周可实习不少于 {self.profile.min_days_per_week} 天")
        return tuple(highlights[:3])


class JobSearchAgentSkills:
    """Facade combining filtering and greeting-writing skills."""

    def __init__(self, profile: CandidateProfile, threshold: int = 65) -> None:
        self.profile = profile
        self.filter_skill = JobFilterSkill(profile, threshold=threshold)
        self.greeting_skill = GreetingWriterSkill(profile)

    def recommend_and_greet(
        self,
        jobs: Iterable[JobPosting | Mapping[str, Any]],
        tone: Tone = Tone.PROFESSIONAL,
    ) -> list[GreetingDraft]:
        """Filter jobs and generate greetings for recommended postings."""

        return [self.greeting_skill.draft(match, tone=tone) for match in self.filter_skill.filter(jobs)]


def build_default_undergraduate_profile(
    name: str = "张同学",
    school: str = "某某大学",
    contact: str = "",
) -> CandidateProfile:
    """Create a ready-to-use profile for a CS undergraduate internship search."""

    return CandidateProfile(name=name, school=school, contact=contact)


def _ensure_job(job: JobPosting | Mapping[str, Any]) -> JobPosting:
    if isinstance(job, JobPosting):
        return job
    return JobPosting.from_mapping(job)


def _parse_work_mode(value: str) -> WorkMode:
    normalized = value.strip().lower()
    if normalized in {"remote", "远程", "居家"}:
        return WorkMode.REMOTE
    if normalized in {"hybrid", "混合", "弹性"}:
        return WorkMode.HYBRID
    if normalized in {"onsite", "office", "现场", "到岗"}:
        return WorkMode.ONSITE
    return WorkMode.UNKNOWN


def _parse_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _split_keywords(value: str) -> list[str]:
    for separator in ("，", "、", ";", "|", "/"):
        value = value.replace(separator, ",")
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _keyword_hits(text: str, keywords: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    hits: list[str] = []
    for keyword in keywords:
        normalized = keyword.lower()
        if normalized and normalized in text and normalized not in seen:
            seen.add(normalized)
            hits.append(keyword)
    return tuple(hits)


def _skill_overlap(
    candidate_skills: Sequence[str],
    required_skills: Sequence[str],
    searchable_text: str,
) -> tuple[str, ...]:
    required_text = _normalize_text(" ".join(required_skills))
    combined_text = f"{required_text} {searchable_text}"
    return _keyword_hits(combined_text, candidate_skills)


def _join_cn(items: Sequence[str]) -> str:
    if not items:
        return "有相关项目经验"
    if len(items) == 1:
        return items[0]
    return "、".join(items[:-1]) + "，以及" + items[-1]


def _trim_to_sentence(message: str, max_chars: int) -> str:
    if len(message) <= max_chars:
        return message
    trimmed = message[: max(0, max_chars - 1)].rstrip("，；、 ")
    return trimmed + "…"


if __name__ == "__main__":
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
