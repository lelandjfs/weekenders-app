"""
Web Search Tool for LangChain Dining Agent
============================================

LangChain-compatible tool for searching restaurant recommendations.
Uses Parallel AI for 10x faster searches with pre-structured results.
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langsmith import traceable

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weekender"))
from parallel_search import search_restaurants, get_page_contents


class WebSearchInput(BaseModel):
    """Input schema for web search."""
    city: str = Field(description="City name to search for")
    neighborhoods: List[str] = Field(
        default=[],
        description="List of neighborhoods to include in search"
    )


@tool(args_schema=WebSearchInput)
@traceable(name="parallel_web_restaurants_api", run_type="tool")
def search_web_restaurants(
    city: str,
    neighborhoods: List[str] = None
) -> List[str]:
    """
    Search web sources for restaurant recommendations using Parallel AI.

    Searches Eater, The Infatuation, Reddit, Yelp and more for best
    restaurant lists and recommendations. Returns pre-structured excerpts.

    Args:
        city: City name (e.g., "San Francisco")
        neighborhoods: Optional list of neighborhoods to include

    Returns:
        List of page contents (structured excerpts from sources)
    """
    if neighborhoods is None:
        neighborhoods = []

    print(f"   -> Searching Parallel AI for {city} restaurants...")

    # Get structured results from Parallel AI
    results = search_restaurants(city, neighborhoods)

    print(f"   -> Found {len(results)} sources")

    if not results:
        return []

    # Convert to page content format for aggregation
    page_contents = get_page_contents(results)

    print(f"   -> Extracted content from {len(page_contents)} sources")

    return page_contents
