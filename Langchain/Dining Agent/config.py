"""
Configuration for LangChain Dining Agent
==========================================

Manages API keys, LangSmith setup, and environment configuration.
"""

import os
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
    project_name: str = "weekenders-dining-agent",
    tracing_enabled: bool = True
):
    """
    Configure LangSmith tracing for observability.

    Args:
        project_name: Name of the LangSmith project
        tracing_enabled: Whether to enable tracing

    Environment variables used:
        - LANGSMITH_API_KEY: Your LangSmith API key
        - LANGSMITH_TRACING: Set to "true" to enable
        - LANGSMITH_PROJECT: Project name for grouping traces
    """
    if tracing_enabled:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        if project_name:
            os.environ["LANGSMITH_PROJECT"] = project_name

        # Check for API key
        if not os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
            print("Warning: LANGSMITH_API_KEY not set. Tracing will not work.")
            print("Set it via: export LANGSMITH_API_KEY='your-key'")
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


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


# =============================================================================
# Neighborhood Discovery Settings
# =============================================================================

MAX_NEIGHBORHOODS = 5
