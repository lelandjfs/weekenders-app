"""
Web Search Tool for LangChain Locations Agent
===============================================

LangChain-compatible tool for searching hidden gems and local attractions.
Uses Parallel AI for 10x faster searches with pre-structured results.

Focused on younger, local tourist vibes - not generic tourist trap lists.
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langsmith import traceable

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weekender"))
from parallel_search import search_locations, get_page_contents


class WebSearchLocationsInput(BaseModel):
    """Input schema for web locations search."""
    city: str = Field(description="City name to search for")


@tool(args_schema=WebSearchLocationsInput)
@traceable(name="parallel_web_locations_api", run_type="tool")
def search_web_locations(city: str) -> List[str]:
    """
    Search web sources for hidden gems and local attractions using Parallel AI.

    Sources prioritized for authentic, local tourist experience:
    - Reddit: Local subreddits for insider recommendations
    - Timeout: Curated city guides
    - Atlas Obscura: Unusual and hidden spots
    - Conde Nast Traveler: Quality travel recommendations
    - Travel + Leisure: Popular attractions

    Args:
        city: City name (e.g., "San Francisco", "Austin")

    Returns:
        List of page contents (structured excerpts from sources)
    """
    print(f"   -> Searching Parallel AI for {city} locations...")

    # Get structured results from Parallel AI
    results = search_locations(city)

    print(f"   -> Found {len(results)} sources")

    if not results:
        return []

    # Convert to page content format for aggregation
    page_contents = get_page_contents(results)

    print(f"   -> Extracted content from {len(page_contents)} sources")

    return page_contents
