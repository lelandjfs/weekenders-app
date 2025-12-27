"""
Configuration for LangChain Concert Agent
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

# Ticketmaster Discovery API
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")

# Tavily API for web search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Anthropic API (for Claude)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# OpenAI API (optional, for GPT models)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# =============================================================================
# LangSmith Configuration
# =============================================================================

def setup_langsmith(
    project_name: str = "weekenders-concert-agent",
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
# Concert Domains Configuration
# =============================================================================

# Domains to search for concert listings
CONCERT_DOMAINS = {
    "songkick.com": "/concerts/",
    "bandsintown.com": "/e/",
    "seatgeek.com": "/concert/",
}

# Venue discovery query templates by genre
VENUE_DISCOVERY_QUERIES = [
    # General / Indie
    "best indie concert venues {city}",
    "small live music venues {city}",
    "underground music venues {city}",
    # Electronic / Dance
    "best EDM clubs {city}",
    "electronic music venues {city}",
    # Country / Americana
    "honky tonk bars {city}",
    "country music venues {city}",
    # Jazz / Blues
    "jazz clubs {city}",
    "blues venues {city}",
]


# =============================================================================
# Default Settings
# =============================================================================

# Maximum venues to discover per location
MAX_VENUES_TO_DISCOVER = 5

# Maximum pages to extract from web search
MAX_PAGES_TO_EXTRACT = 15

# Ticketmaster results limit
TICKETMASTER_RESULTS_LIMIT = 50
