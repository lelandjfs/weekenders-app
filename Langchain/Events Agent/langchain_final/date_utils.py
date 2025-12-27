"""
Date Utilities for Events Agent
================================

Calculates weekend date ranges for event searches.
Events use Friday - Sunday (unlike concerts which use Thu-Sat).
"""

from datetime import datetime, timedelta
from typing import Tuple


def get_events_weekend_dates(weekend: str = "next") -> Tuple[str, str]:
    """
    Get the Friday-Sunday date range for events.

    Events typically run Friday through Sunday, including:
    - Saturday daytime activities
    - Sunday family events
    - Weekend festivals

    Args:
        weekend: "next" for upcoming weekend, "this" for current week

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    current_weekday = today.weekday()  # Monday = 0, Sunday = 6

    if weekend == "this":
        # This weekend's Friday
        if current_weekday <= 4:  # Mon-Fri
            days_until_friday = 4 - current_weekday
        else:  # Already Sat or Sun
            days_until_friday = -(current_weekday - 4)
    else:
        # Next weekend's Friday
        if current_weekday <= 3:  # Mon-Thu: this week's Friday
            days_until_friday = 4 - current_weekday
        else:  # Fri-Sun: next week's Friday
            days_until_friday = 11 - current_weekday

    friday = today + timedelta(days=days_until_friday)
    sunday = friday + timedelta(days=2)

    return friday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def get_weekend_dates_for_display(weekend: str = "next") -> str:
    """
    Get a human-readable weekend date string.
    """
    start_date, end_date = get_events_weekend_dates(weekend)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    return f"{start.strftime('%A, %b %d')} - {end.strftime('%A, %b %d')}"


if __name__ == "__main__":
    print("Events Weekend Dates (Fri-Sun)")
    print("=" * 40)

    this_start, this_end = get_events_weekend_dates("this")
    print(f"This weekend: {this_start} to {this_end}")

    next_start, next_end = get_events_weekend_dates("next")
    print(f"Next weekend: {next_start} to {next_end}")
