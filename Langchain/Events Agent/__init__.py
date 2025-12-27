"""
LangChain Events Agent
=======================

A LangChain-compatible agent for discovering local events.
Covers sports, theater, comedy, festivals, and family events.
"""

from .date_utils import get_events_weekend_dates

__all__ = ["get_events_weekend_dates"]
