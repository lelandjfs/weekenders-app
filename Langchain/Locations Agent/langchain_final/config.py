"""
Configuration for LangChain Locations Agent
=============================================

Manages API keys, LangSmith setup, and environment configuration.
Focused on non-date-specific attractions: museums, gardens, landmarks, hidden gems.
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

# Google Places API
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY")

# Tavily API for web search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Anthropic API (for Claude Haiku)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# =============================================================================
# LangSmith Configuration
# =============================================================================

def setup_langsmith(
    project_name: str = "weekenders-locations-agent",
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
        print(f"   Warning: Geocoding error for {city}: {e}")

    return None


# =============================================================================
# Google Places Settings - Attractions & Locations
# =============================================================================

# Place types to search for attractions (non-date-specific)
# Focused on younger, local tourist vibes - hidden gems, not generic tourist traps
ATTRACTION_TYPES = [
    "tourist_attraction",
    "museum",
    "art_gallery",
    "park",
    "hiking_area",
    "botanical_garden",
    "zoo",
    "aquarium",
    "amusement_park",
    "landmark",
    "historical_landmark",
    "cultural_center",
    "performing_arts_theater",
    "observation_deck",
    "marina",
    "beach",
    "national_park",
    "state_park",
    "city_hall",  # Often architecturally interesting
    "library",    # Many cities have beautiful historic libraries
]

# Fields to request from Google Places API
GOOGLE_PLACES_FIELDS = [
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.types",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.regularOpeningHours",
    "places.primaryType",
    "places.editorialSummary",
    "places.photos",
]

# Minimum rating to include (1-5) - lower for attractions since they're unique
MIN_RATING = 3.5

# Minimum number of reviews
MIN_REVIEWS = 20

# Maximum results per search type
MAX_RESULTS_PER_TYPE = 10

# Search radius in meters (5 miles = ~8000m, but we want broader for attractions)
DEFAULT_SEARCH_RADIUS = 15000  # ~10 miles


# =============================================================================
# Web Search Settings - Local Tourist Vibes
# =============================================================================

# Sources prioritized for younger, local tourist experience
WEB_SEARCH_SOURCES = {
    "reddit": {
        "domain": "reddit.com",
        "queries": [
            "hidden gems {city} site:reddit.com",
            "best things to do {city} locals site:reddit.com",
            "underrated spots {city} site:reddit.com",
            "cool places to visit {city} site:reddit.com",
        ]
    },
    "timeout": {
        "domain": "timeout.com",
        "queries": [
            "best things to do {city} site:timeout.com",
            "hidden gems {city} site:timeout.com",
            "free things to do {city} site:timeout.com",
        ]
    },
    "atlas_obscura": {
        "domain": "atlasobscura.com",
        "queries": [
            "{city} site:atlasobscura.com",
            "unusual things {city} site:atlasobscura.com",
        ]
    },
    "conde_nast": {
        "domain": "cntraveler.com",
        "queries": [
            "things to do {city} site:cntraveler.com",
            "best of {city} site:cntraveler.com",
        ]
    },
    "travel_leisure": {
        "domain": "travelandleisure.com",
        "queries": [
            "things to do {city} site:travelandleisure.com",
        ]
    },
}

MAX_WEB_RESULTS_PER_SOURCE = 8
MAX_PAGES_TO_EXTRACT = 15


# =============================================================================
# Attraction Categories for Classification
# =============================================================================

ATTRACTION_CATEGORIES = {
    "Museums & Art": ["museum", "art_gallery", "cultural_center"],
    "Nature & Parks": ["park", "botanical_garden", "hiking_area", "beach", "national_park", "state_park"],
    "Wildlife": ["zoo", "aquarium"],
    "Landmarks": ["landmark", "historical_landmark", "tourist_attraction", "observation_deck"],
    "Entertainment": ["amusement_park", "performing_arts_theater"],
    "Architecture": ["city_hall", "library", "marina"],
    "Hidden Gems": [],  # Web search results go here
}
