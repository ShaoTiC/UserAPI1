"""World Cup match-schedule email agent."""

from .agent import WorldCupEmailAgent, run_once
from .config import AgentConfig
from .schedule import Match, ScheduleClient

__all__ = [
    "AgentConfig",
    "Match",
    "ScheduleClient",
    "WorldCupEmailAgent",
    "run_once",
]

__version__ = "1.0.0"
