"""
Date Utilities for Weekenders App
=================================

Calculates weekend date ranges for each agent type.
Each agent has specific date ranges based on content type:

- Concert Agent: Thu - Sat (concerts peak Thu-Sat nights)
- Events Agent: Fri - Sun (general events include Sunday)
- Dining Agent: Fri - Sun (weekend dining + Sunday brunch)
- Locations Agent: Fri - Sun (attractions open all weekend)
"""

from datetime import datetime, timedelta
from typing import Tuple
from enum import Enum


class AgentType(Enum):
    CONCERT = "concert"      # Thu - Sat
    EVENTS = "events"        # Fri - Sun
    DINING = "dining"        # Fri - Sun
    LOCATIONS = "locations"  # Fri - Sun


def get_next_saturday(from_date: datetime = None) -> datetime:
    """
    Get the NEXT Saturday (always at least 7 days out if currently Thu-Sun).

    "Next weekend" always means the weekend AFTER the immediate one.
    Use get_this_saturday() if you want the current/immediate weekend.
    """
    if from_date is None:
        from_date = datetime.now()

    day_of_week = from_date.weekday()

    # Always go to next week's Saturday (7+ days out)
    days_until_saturday = (5 - day_of_week) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7  # If today is Saturday, go to next Saturday

    # If we're in Thu-Sun, add a week to get "next" weekend
    if day_of_week >= 3:  # Thu=3, Fri=4, Sat=5, Sun=6
        days_until_saturday += 7

    return from_date + timedelta(days=days_until_saturday)


def get_this_saturday(from_date: datetime = None) -> datetime:
    """
    Get THIS week's Saturday (the immediate/current weekend).

    If today is Sunday, returns yesterday (Saturday).
    """
    if from_date is None:
        from_date = datetime.now()

    day_of_week = from_date.weekday()

    if day_of_week == 6:  # Sunday - go back to Saturday
        return from_date - timedelta(days=1)

    # Calculate days until Saturday
    days_until_saturday = (5 - day_of_week) % 7
    if days_until_saturday == 0 and day_of_week != 5:
        days_until_saturday = 7

    return from_date + timedelta(days=days_until_saturday)


def get_weekend_dates(
    agent_type: AgentType = AgentType.CONCERT,
    weekend: str = "next",
    from_date: datetime = None
) -> Tuple[str, str]:
    """
    Get the start and end dates for a weekend based on agent type.

    Args:
        agent_type: Type of agent (determines date range)
        weekend: "next" for next weekend, "this" for current week
        from_date: Optional reference date (defaults to today)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format

    Examples:
        >>> get_weekend_dates(AgentType.CONCERT)  # Today is Wed Dec 25
        ('2026-01-02', '2026-01-04')  # Thu - Sat

        >>> get_weekend_dates(AgentType.EVENTS)   # Today is Wed Dec 25
        ('2026-01-03', '2026-01-05')  # Fri - Sun
    """
    if from_date is None:
        from_date = datetime.now()

    # Get the target Saturday
    if weekend == "this":
        target_saturday = get_this_saturday(from_date)
    else:  # "next" weekend
        target_saturday = get_next_saturday(from_date)

    # Calculate start and end based on agent type
    if agent_type == AgentType.CONCERT:
        # Thu - Sat (Saturday - 2 days to Saturday)
        start_date = target_saturday - timedelta(days=2)  # Thursday
        end_date = target_saturday  # Saturday
    else:
        # Fri - Sun (Saturday - 1 day to Saturday + 1 day)
        start_date = target_saturday - timedelta(days=1)  # Friday
        end_date = target_saturday + timedelta(days=1)    # Sunday

    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def get_concert_weekend_dates(weekend: str = "next", from_date: datetime = None) -> Tuple[str, str]:
    """Convenience function for Concert Agent: Thu - Sat"""
    return get_weekend_dates(AgentType.CONCERT, weekend, from_date)


def get_events_weekend_dates(weekend: str = "next", from_date: datetime = None) -> Tuple[str, str]:
    """Convenience function for Events Agent: Fri - Sun"""
    return get_weekend_dates(AgentType.EVENTS, weekend, from_date)


def get_dining_weekend_dates(weekend: str = "next", from_date: datetime = None) -> Tuple[str, str]:
    """Convenience function for Dining Agent: Fri - Sun"""
    return get_weekend_dates(AgentType.DINING, weekend, from_date)


def get_locations_weekend_dates(weekend: str = "next", from_date: datetime = None) -> Tuple[str, str]:
    """Convenience function for Locations Agent: Fri - Sun"""
    return get_weekend_dates(AgentType.LOCATIONS, weekend, from_date)
