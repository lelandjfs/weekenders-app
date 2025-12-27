"""
Concert Agent Schemas
=====================

Pydantic models for concert data structures.
Shared across all tools for consistent typing.
"""

from typing import List, Optional
from pydantic import BaseModel


class Concert(BaseModel):
    """Individual concert schema"""
    name: str
    venue: str
    date: str  # YYYY-MM-DD
    time: Optional[str] = None  # e.g., "8:00 PM"
    location: str  # City, State
    price_range: Optional[str] = None  # e.g., "$50-$150"
    url: Optional[str] = None
    source: str  # "ticketmaster" or "web"
    genre: Optional[str] = None


class ConcertResults(BaseModel):
    """Complete concert results schema"""
    concerts: List[Concert]
    total_count: int
    date_range: str
    search_location: str
    search_radius_miles: float
