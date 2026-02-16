"""
Web Search Tool for LangChain Events Agent
============================================

LangChain-compatible tool for searching local events.
Uses Parallel AI for 10x faster searches with pre-structured results.
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langsmith import traceable

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weekender"))
from parallel_search import search_events, get_page_contents


class WebSearchEventsInput(BaseModel):
    """Input schema for web events search."""
    city: str = Field(description="City name to search for")
    start_date: str = Field(description="Start date for context")
    end_date: str = Field(description="End date for context")


@tool(args_schema=WebSearchEventsInput)
@traceable(name="parallel_web_events_api", run_type="tool")
def search_web_events(
    city: str,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    Search web sources for local events using Parallel AI.

    Searches Eventbrite, Timeout, and general web for events,
    festivals, and things to do. Returns pre-structured excerpts.

    Args:
        city: City name (e.g., "San Francisco")
        start_date: Start date for search context
        end_date: End date for search context

    Returns:
        List of page contents (structured excerpts from sources)
    """
    print(f"   -> Searching Parallel AI for {city} events ({start_date} to {end_date})...")

    # Get structured results from Parallel AI
    results = search_events(city, start_date, end_date)

    print(f"   -> Found {len(results)} sources")

    if not results:
        return []

    # Convert to page content format for aggregation
    page_contents = get_page_contents(results)

    print(f"   -> Extracted content from {len(page_contents)} sources")

    return page_contents
