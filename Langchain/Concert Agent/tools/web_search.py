"""
Web Search Tool for LangChain Concert Agent
=============================================

LangChain-compatible tool for searching concerts and live music.
Uses Parallel AI for 10x faster searches with pre-structured results.
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langsmith import traceable

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weekender"))
from parallel_search import search_concerts, get_page_contents, discover_venues as _discover_venues


class WebSearchConcertsInput(BaseModel):
    """Input schema for web concerts search."""
    city: str = Field(description="City name to search for")
    start_date: str = Field(description="Start date (YYYY-MM-DD)")
    end_date: str = Field(description="End date (YYYY-MM-DD)")


class VenueDiscoveryInput(BaseModel):
    """Input schema for venue discovery."""
    city: str = Field(description="City name to discover venues for")
    max_venues: int = Field(default=5, description="Maximum number of venues to discover")


@tool(args_schema=WebSearchConcertsInput)
@traceable(name="parallel_web_concerts_api", run_type="tool")
def search_web_concerts(
    city: str,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    Search web sources for concerts and live music using Parallel AI.

    Searches Songkick, Bandsintown, SeatGeek and more for concerts,
    shows, and live music events. Returns pre-structured excerpts.

    Args:
        city: City name (e.g., "San Francisco")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of page contents (structured excerpts from sources)
    """
    print(f"   -> Searching Parallel AI for {city} concerts ({start_date} to {end_date})...")

    # Get structured results from Parallel AI
    results = search_concerts(city, start_date, end_date)

    print(f"   -> Found {len(results)} sources")

    if not results:
        return []

    # Convert to page content format for aggregation
    page_contents = get_page_contents(results)

    print(f"   -> Extracted content from {len(page_contents)} sources")

    return page_contents


@tool(args_schema=VenueDiscoveryInput)
@traceable(name="parallel_discover_venues", run_type="tool")
def discover_venues(city: str, max_venues: int = 5) -> List[str]:
    """
    Discover indie/small concert venues for any city using Parallel AI.

    Searches across multiple genres (indie, EDM, jazz, blues)
    to find venue names.

    Args:
        city: City name to discover venues for
        max_venues: Maximum number of venues to return

    Returns:
        List of venue names discovered for the city
    """
    print(f"   -> Discovering venues in {city} via Parallel AI...")

    venues = _discover_venues(city, max_venues)

    print(f"   -> Found {len(venues)} venues")

    return venues
