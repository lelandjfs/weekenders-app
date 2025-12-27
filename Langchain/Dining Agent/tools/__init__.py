"""
Dining Agent Tools
==================

Tools for restaurant discovery:
- Neighborhood discovery
- Google Places search
- Web search (Eater, Reddit, Infatuation)
- Aggregation with Claude Haiku
"""

from .neighborhood_discovery import discover_neighborhoods
from .google_places import search_google_places
from .web_search import search_web_restaurants
from .aggregation import aggregate_restaurants

__all__ = [
    "discover_neighborhoods",
    "search_google_places",
    "search_web_restaurants",
    "aggregate_restaurants",
]
