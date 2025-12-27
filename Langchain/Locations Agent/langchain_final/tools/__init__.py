"""
LangChain Tools for Locations Agent
=====================================

Tools for discovering attractions and locations:
- google_places: Search Google Places API for attractions
- web_search: Search Reddit, Timeout, Atlas Obscura for hidden gems
- aggregation: Combine and deduplicate results with Claude Haiku
"""

from .google_places import search_google_places_attractions
from .web_search import search_web_locations
from .aggregation import aggregate_locations

__all__ = [
    "search_google_places_attractions",
    "search_web_locations",
    "aggregate_locations",
]
