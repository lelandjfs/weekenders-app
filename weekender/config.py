"""
Configuration for Weekender App
================================

Consolidated config for all agents. Includes settings from:
- Concert Agent
- Dining Agent
- Events Agent
- Locations Agent
"""

import os
import requests
from typing import Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from timezonefinder import TimezoneFinder

# Load environment variables from parent .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# =============================================================================
# API Keys
# =============================================================================

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# =============================================================================
# LangSmith Configuration
# =============================================================================

def setup_langsmith(project_name: str = "weekenders-app"):
    """Configure LangSmith tracing."""
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_PROJECT"] = project_name

    if LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        print(f"LangSmith tracing enabled for project: {project_name}")
    else:
        print("Warning: LANGSMITH_API_KEY not set")


# =============================================================================
# City Coordinates Cache
# =============================================================================

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
    "new orleans": (29.9511, -90.0715),
    "minneapolis": (44.9778, -93.2650),
    "detroit": (42.3314, -83.0458),
}


def get_city_coordinates(city: str) -> Optional[Tuple[float, float]]:
    """Get coordinates for any city dynamically."""
    city_lower = city.lower().strip()
    city_base = city_lower.split(",")[0].strip()

    if city_base in _CITY_CACHE:
        return _CITY_CACHE[city_base]

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": city,
                "format": "json",
                "limit": 1,
                "countrycodes": "us",
            },
            headers={"User-Agent": "WeekendersApp/1.0"},
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            _CITY_CACHE[city_base] = (lat, lon)
            return (lat, lon)
    except Exception:
        pass

    return None


# =============================================================================
# Timezone Utilities
# =============================================================================

_tz_finder = TimezoneFinder()

def get_local_ticketmaster_dates(lat: float, lon: float, start_date: str, end_date: str) -> Tuple[str, str]:
    """Convert date range to UTC datetimes based on the location's local timezone.

    Ticketmaster expects UTC (Z suffix). This ensures midnight local time
    is correctly converted to UTC so results match the intended date range.

    Args:
        lat: Latitude of the search location
        lon: Longitude of the search location
        start_date: Start date as YYYY-MM-DD
        end_date: End date as YYYY-MM-DD

    Returns:
        Tuple of (start_datetime_utc, end_datetime_utc) formatted for Ticketmaster
    """
    tz_name = _tz_finder.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        # Fallback: no Z suffix lets Ticketmaster use venue local time
        return f"{start_date}T00:00:00", f"{end_date}T23:59:59"

    local_tz = ZoneInfo(tz_name)
    utc = ZoneInfo("UTC")

    # Local midnight start -> UTC
    local_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=local_tz)
    utc_start = local_start.astimezone(utc)

    # Local end of day -> UTC
    local_end = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
    utc_end = local_end.astimezone(utc)

    return utc_start.strftime("%Y-%m-%dT%H:%M:%SZ"), utc_end.strftime("%Y-%m-%dT%H:%M:%SZ")


# =============================================================================
# Concert Agent Settings
# =============================================================================

CONCERT_DOMAINS = {
    "songkick.com": "/concerts/",
    "bandsintown.com": "/e/",
    "seatgeek.com": "/concert/",
}

VENUE_DISCOVERY_QUERIES = [
    "best indie concert venues {city}",
    "small live music venues {city}",
    "underground music venues {city}",
    "best EDM clubs {city}",
    "electronic music venues {city}",
    "honky tonk bars {city}",
    "country music venues {city}",
    "jazz clubs {city}",
    "blues venues {city}",
]

MAX_VENUES_TO_DISCOVER = 5
MAX_PAGES_TO_EXTRACT = 15
TICKETMASTER_RESULTS_LIMIT = 50


# =============================================================================
# Dining Agent Settings
# =============================================================================

GOOGLE_PLACES_FIELDS = [
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.types",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.regularOpeningHours",
    "places.primaryType",
    "places.editorialSummary",
    "places.photos",
]

MIN_RATING = 4.0
MIN_REVIEWS = 50
MAX_RESULTS_PER_NEIGHBORHOOD = 10
MAX_NEIGHBORHOODS = 5
MAX_WEB_RESULTS_PER_SOURCE = 10

# Dining web sources
WEB_SEARCH_SOURCES = {
    "eater": {
        "domain": "eater.com",
        "queries": [
            "best restaurants {city} site:eater.com",
            "new restaurants {city} site:eater.com",
            "where to eat {city} site:eater.com",
        ]
    },
    "infatuation": {
        "domain": "theinfatuation.com",
        "queries": [
            "best restaurants {city} site:theinfatuation.com",
            "{city} restaurant guide site:theinfatuation.com",
        ]
    },
    "reddit": {
        "domain": "reddit.com",
        "queries": [
            "best restaurants {city} site:reddit.com",
            "where to eat {city} site:reddit.com",
            "food recommendations {city} site:reddit.com",
        ]
    },
}


# =============================================================================
# Events Agent Settings
# =============================================================================

EVENT_CLASSIFICATIONS = [
    "Sports",
    "Arts & Theatre",
    "Film",
    "Miscellaneous",
    "Family",
]

CLASSIFICATION_IDS = {
    "sports": "KZFzniwnSyZfZ7v7nE",
    "arts": "KZFzniwnSyZfZ7v7na",
    "family": "KZFzniwnSyZfZ7v7n1",
    "film": "KZFzniwnSyZfZ7v7nn",
    "misc": "KZFzniwnSyZfZ7v7n1",
}

DEFAULT_SEARCH_RADIUS = 25


# =============================================================================
# Locations Agent Settings
# =============================================================================

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
    "city_hall",
    "library",
]

MAX_RESULTS_PER_TYPE = 10

ATTRACTION_CATEGORIES = {
    "Museums & Art": ["museum", "art_gallery", "cultural_center"],
    "Nature & Parks": ["park", "botanical_garden", "hiking_area", "beach", "national_park", "state_park"],
    "Wildlife": ["zoo", "aquarium"],
    "Landmarks": ["landmark", "historical_landmark", "tourist_attraction", "observation_deck"],
    "Entertainment": ["amusement_park", "performing_arts_theater"],
    "Architecture": ["city_hall", "library", "marina"],
    "Hidden Gems": [],
}
