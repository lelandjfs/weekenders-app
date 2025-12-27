"""
Configuration for Dining Agent
===============================

API keys and settings for restaurant discovery.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# API Keys
# =============================================================================

GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# =============================================================================
# Neighborhood Discovery Settings
# =============================================================================

NEIGHBORHOOD_DISCOVERY_QUERIES = [
    "trendy neighborhoods {city}",
    "best food neighborhoods {city}",
    "hipster neighborhoods {city}",
    "up and coming neighborhoods {city}",
    "best areas to eat {city}",
]

MAX_NEIGHBORHOODS = 5

# =============================================================================
# Google Places Settings
# =============================================================================

# Fields to request from Google Places API
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
]

# Minimum rating to include (1-5)
MIN_RATING = 4.0

# Minimum number of reviews to include
MIN_REVIEWS = 50

# Maximum results per neighborhood
MAX_RESULTS_PER_NEIGHBORHOOD = 10

# =============================================================================
# Web Search Settings
# =============================================================================

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

MAX_WEB_RESULTS_PER_SOURCE = 10
MAX_PAGES_TO_EXTRACT = 15
