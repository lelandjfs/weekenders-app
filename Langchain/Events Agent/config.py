"""
Configuration for LangChain Events Agent
==========================================

Manages API keys, LangSmith setup, and environment configuration.
"""

import os
import requests
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# =============================================================================
# API Keys
# =============================================================================

# Ticketmaster Discovery API
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")

# Tavily API for web search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Anthropic API (for Claude Haiku)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# =============================================================================
# LangSmith Configuration
# =============================================================================

def setup_langsmith(
    project_name: str = "weekenders-events-agent",
    tracing_enabled: bool = True
):
    """
    Configure LangSmith tracing for observability.
    """
    if tracing_enabled:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        if project_name:
            os.environ["LANGSMITH_PROJECT"] = project_name

        if not os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
            print("Warning: LANGSMITH_API_KEY not set. Tracing will not work.")
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


# =============================================================================
# Dynamic Geocoding
# =============================================================================

# Cache of common cities (fast lookup)
_CITY_CACHE = {
    "san francisco": (37.7749, -122.4194),
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "austin": (30.2672, -97.7431),
    "chicago": (41.8781, -87.6298),
    "seattle": (47.6062, -122.3321),
    "boston": (42.3601, -71.0589),
    "denver": (39.7392, -104.9903),
    "miami": (25.7617, -80.1918),
    "portland": (45.5152, -122.6784),
    "sacramento": (38.5816, -121.4944),
    "san diego": (32.7157, -117.1611),
    "phoenix": (33.4484, -112.0740),
    "las vegas": (36.1699, -115.1398),
    "nashville": (36.1627, -86.7816),
    "atlanta": (33.7490, -84.3880),
    "dallas": (32.7767, -96.7970),
    "houston": (29.7604, -95.3698),
    "philadelphia": (39.9526, -75.1652),
    "washington dc": (38.9072, -77.0369),
}


def get_city_coordinates(city: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for any city dynamically.

    First checks local cache, then falls back to Nominatim (OpenStreetMap)
    for any city worldwide.

    Args:
        city: City name (e.g., "Sacramento", "San Diego, CA")

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    # Normalize city name
    city_lower = city.lower().strip()

    # Remove state/country suffixes for cache lookup
    city_base = city_lower.split(",")[0].strip()

    # Check cache first
    if city_base in _CITY_CACHE:
        return _CITY_CACHE[city_base]

    # Fall back to Nominatim (OpenStreetMap) - FREE, no API key needed
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": city,
                "format": "json",
                "limit": 1,
                "countrycodes": "us",  # Prioritize US results
            },
            headers={
                "User-Agent": "WeekendersApp/1.0"  # Required by Nominatim
            },
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            # Cache for future use
            _CITY_CACHE[city_base] = (lat, lon)
            return (lat, lon)

    except Exception as e:
        print(f"   ⚠️ Geocoding error for {city}: {e}")

    return None


# =============================================================================
# Ticketmaster Settings
# =============================================================================

# Event classifications to search (non-music)
EVENT_CLASSIFICATIONS = [
    "Sports",
    "Arts & Theatre",
    "Film",
    "Miscellaneous",
    "Family",
]

# Classification IDs for Ticketmaster API
# https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/#classifications
CLASSIFICATION_IDS = {
    "sports": "KZFzniwnSyZfZ7v7nE",      # Sports
    "arts": "KZFzniwnSyZfZ7v7na",         # Arts & Theatre
    "family": "KZFzniwnSyZfZ7v7n1",       # Family
    "film": "KZFzniwnSyZfZ7v7nn",         # Film
    "misc": "KZFzniwnSyZfZ7v7n1",         # Miscellaneous
}

TICKETMASTER_RESULTS_LIMIT = 50
DEFAULT_SEARCH_RADIUS = 25


# =============================================================================
# Web Search Settings
# =============================================================================

WEB_SEARCH_SOURCES = {
    "eventbrite": {
        "domain": "eventbrite.com",
        "queries": [
            "events {city} this weekend site:eventbrite.com",
            "things to do {city} site:eventbrite.com",
            "festivals {city} site:eventbrite.com",
        ]
    },
    "timeout": {
        "domain": "timeout.com",
        "queries": [
            "things to do {city} site:timeout.com",
            "events {city} this weekend site:timeout.com",
        ]
    },
    "general": {
        "domain": None,
        "queries": [
            "events this weekend {city}",
            "things to do this weekend {city}",
        ]
    },
}

MAX_WEB_RESULTS_PER_SOURCE = 10
MAX_PAGES_TO_EXTRACT = 15
