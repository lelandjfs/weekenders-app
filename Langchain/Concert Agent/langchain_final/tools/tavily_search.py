"""
Tavily Web Search Tool for LangChain
=====================================

LangChain-compatible tools for web-based concert discovery.
Uses @tool decorator for LangSmith tracing.

Features:
- Dynamic venue discovery for any location
- Day-by-day search for better date coverage
- Multi-domain search (Songkick, Bandsintown, SeatGeek)
- Event page filtering (skips listing pages)
"""

import requests
import re
from typing import List, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.tools import tool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TAVILY_API_KEY,
    CONCERT_DOMAINS,
    VENUE_DISCOVERY_QUERIES,
    MAX_VENUES_TO_DISCOVER,
    MAX_PAGES_TO_EXTRACT
)


# =============================================================================
# Input Schemas
# =============================================================================

class VenueDiscoveryInput(BaseModel):
    """Input schema for venue discovery."""
    city: str = Field(description="City name to discover venues for")
    max_venues: int = Field(
        default=5,
        description="Maximum number of venues to discover"
    )


class WebConcertSearchInput(BaseModel):
    """Input schema for web concert search."""
    city: str = Field(description="City to search concerts in")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    venues: List[str] = Field(
        default=[],
        description="Optional list of specific venues to search"
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _get_dates_in_range(start_date: str, end_date: str) -> List[str]:
    """Generate list of dates between start and end (inclusive)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def _format_date_for_search(date_str: str) -> str:
    """Format date for better search engine understanding."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d %Y").replace(" 0", " ")


def _search_tavily(query: str, domains: List[str], max_results: int = 15) -> List[dict]:
    """Execute a single Tavily search query."""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "include_domains": domains,
                "max_results": max_results,
                "search_depth": "advanced"
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception:
        return []


def _is_event_page(url: str) -> bool:
    """Check if URL is an event detail page (not a listing page)."""
    if "songkick.com/concerts/" in url:
        return True
    if "bandsintown.com/e/" in url:
        return True
    if "seatgeek.com" in url and "/concert/" in url:
        return True
    if "seatgeek.com" in url and re.search(r"/tickets/[\w-]+-\d{4}-\d{2}-\d{2}", url):
        return True
    return False


def _extract_venues_from_text(text: str) -> Set[str]:
    """Extract venue names from text using regex patterns."""
    venue_candidates = set()

    patterns = [
        r"The [A-Z][a-z]+(?:\s[A-Z][a-z]+)?",
        r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s(?:Club|Hall|Theater|Theatre|Room|Lounge|Bar|Ballroom|Arena)",
        r"[A-Z][a-z]+\'s",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match.lower() not in ["the city", "the best", "the top", "the most", "the new"]:
                venue_candidates.add(match.strip())

    return venue_candidates


# =============================================================================
# LangChain Tools
# =============================================================================

@tool(args_schema=VenueDiscoveryInput)
def discover_venues(city: str, max_venues: int = 5) -> List[str]:
    """
    Dynamically discover indie/small concert venues for any city.

    Searches across multiple genres (indie, EDM, country, jazz, blues)
    to find venue names, then returns them for venue-specific queries.

    Args:
        city: City name to discover venues for
        max_venues: Maximum number of venues to return

    Returns:
        List of venue names discovered for the city
    """
    venue_candidates: Set[str] = set()

    for query_template in VENUE_DISCOVERY_QUERIES:
        query = query_template.format(city=city)

        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": 10,
                    "search_depth": "basic"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            for result in data.get("results", []):
                text = f"{result.get('title', '')} {result.get('content', '')}"
                venue_candidates.update(_extract_venues_from_text(text))

        except Exception:
            continue

    venues = list(venue_candidates)[:max_venues]
    return venues


@tool(args_schema=WebConcertSearchInput)
def search_web_concerts(
    city: str,
    start_date: str,
    end_date: str,
    venues: List[str] = None
) -> List[str]:
    """
    Search web sources for concerts not on Ticketmaster.

    Uses multi-step search strategy:
    1. Day-by-day queries for each date in range
    2. Venue-specific queries for discovered venues
    3. Filters to only event detail pages
    4. Extracts full page content for parsing

    Args:
        city: City to search concerts in
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        venues: Optional list of specific venues to search

    Returns:
        List of page contents (markdown) from concert listing sites
    """
    if venues is None:
        venues = []

    search_domains = list(CONCERT_DOMAINS.keys())
    all_urls: Set[str] = set()

    # Get individual dates in range
    dates = _get_dates_in_range(start_date, end_date)

    # Build search queries
    search_queries = []

    # Original date-range queries
    search_queries.extend([
        f"concerts near {city} {start_date} site:songkick.com/concerts",
        f"live music near {city} {start_date} site:bandsintown.com/e",
        f"shows near {city} {start_date} to {end_date} site:songkick.com/concerts",
        f"events near {city} {start_date} site:bandsintown.com/e",
    ])

    # Day-by-day queries
    for date in dates:
        friendly_date = _format_date_for_search(date)
        search_queries.extend([
            f"concerts {city} {friendly_date} site:songkick.com/concerts",
            f"live music {city} {friendly_date} site:bandsintown.com/e",
            f"concerts {city} {friendly_date} site:seatgeek.com",
        ])

    # Venue-specific queries
    for venue in venues:
        search_queries.extend([
            f"{venue} {city} concerts {start_date[:7]} site:songkick.com",
            f"{venue} concerts site:bandsintown.com/e",
            f"{venue} {city} site:seatgeek.com",
        ])

    # Execute searches
    for query in search_queries:
        results = _search_tavily(query, search_domains, max_results=10)

        for result in results:
            url = result.get("url", "")
            if _is_event_page(url):
                all_urls.add(url)

    if not all_urls:
        return []

    # Extract content from top URLs
    top_urls = list(all_urls)[:MAX_PAGES_TO_EXTRACT]

    try:
        response = requests.post(
            "https://api.tavily.com/extract",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "urls": top_urls,
                "format": "markdown"
            },
            timeout=45
        )
        response.raise_for_status()
        data = response.json()

        page_contents = []
        for result in data.get("results", []):
            if "raw_content" in result:
                content = f"SOURCE: {result['url']}\n\n{result['raw_content']}"
                page_contents.append(content)

        return page_contents

    except Exception as e:
        print(f"Tavily extract error: {e}")
        return []
