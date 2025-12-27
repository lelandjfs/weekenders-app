"""
LangChain Concert Agent
=======================

A LangChain-compatible concert discovery agent with LangSmith tracing.

This module provides:
- LangChain @tool decorated functions for concert discovery
- Agent orchestration using LangChain patterns
- Full LangSmith observability

Usage:
    from concert_agent import ConcertAgent, run_concert_agent

    agent = ConcertAgent()
    results = agent.run(city, weekend)

Or use date utilities directly:
    from date_utils import get_concert_weekend_dates
"""

# Import date utilities (no external dependencies)
from .date_utils import (
    get_concert_weekend_dates,
    get_weekend_dates,
    AgentType
)

# Lazy imports for agent to avoid circular dependencies
def get_concert_agent():
    """Get ConcertAgent class (lazy import)."""
    from .concert_agent import ConcertAgent
    return ConcertAgent

def get_run_concert_agent():
    """Get run_concert_agent function (lazy import)."""
    from .concert_agent import run_concert_agent
    return run_concert_agent

__all__ = [
    "get_concert_weekend_dates",
    "get_weekend_dates",
    "AgentType",
    "get_concert_agent",
    "get_run_concert_agent",
]
