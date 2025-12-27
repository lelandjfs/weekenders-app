"""
Tavily Tool (SEARCH → EXTRACT)
================================

Two-step web search for indie/small venue concerts.

This tool:
- Searches indie-focused platforms (Songkick, Bandsintown, SeatGeek)
- Dynamically discovers indie venues for any location
- Searches day-by-day for better coverage
- Extracts full page content from concert listing sites
- Returns raw content for Claude to parse
- Captures concerts that Ticketmaster misses (small venues, DIY shows)
"""

import requests
from typing import List, Set
from datetime import datetime, timedelta
import sys
import os
import re

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context_router import SearchContext

# API Key
TAVILY_KEY = "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"

# Supported domains and their event page URL patterns
CONCERT_DOMAINS = {
    "songkick.com": "/concerts/",
    "bandsintown.com": "/e/",
    "seatgeek.com": "/concert/",
}


def _get_dates_in_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate list of dates between start and end (inclusive).

    Args:
        start_date: ISO date (YYYY-MM-DD)
        end_date: ISO date (YYYY-MM-DD)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def _format_date_for_search(date_str: str) -> str:
    """
    Format date for better search engine understanding.
    Converts 2026-01-01 to "January 1 2026"
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d %Y").replace(" 0", " ")  # Remove leading zero from day


def discover_indie_venues(location: str, max_venues: int = 5) -> List[str]:
    """
    Dynamically discover indie/small concert venues for any location.

    Uses web search to find venue names, then returns them for
    venue-specific concert queries.

    Args:
        location: City/location string (e.g., "San Francisco, California, USA")
        max_venues: Maximum number of venues to return

    Returns:
        List of venue names found for the location
    """
    # Extract city name for cleaner searches
    city = location.split(",")[0].strip()

    discovery_queries = [
        # General / Indie
        f"best indie concert venues {city}",
        f"small live music venues {city}",
        f"underground music venues {city}",
        # Electronic / Dance
        f"best EDM clubs {city}",
        f"electronic music venues {city}",
        # Country / Americana
        f"honky tonk bars {city}",
        f"country music venues {city}",
        # Jazz / Blues
        f"jazz clubs {city}",
        f"blues venues {city}",
    ]

    venue_candidates = set()

    for query in discovery_queries:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": TAVILY_KEY,
                    "query": query,
                    "max_results": 10,
                    "search_depth": "basic"  # Faster, cheaper for discovery
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if "results" in data:
                for result in data["results"]:
                    # Extract venue names from titles and snippets
                    text = f"{result.get('title', '')} {result.get('content', '')}"

                    # Look for patterns like "The Midway", "Bottom of the Hill", etc.
                    # Common venue name patterns (The X, X Club, X Hall, X Theater, etc.)
                    patterns = [
                        r"The [A-Z][a-z]+(?:\s[A-Z][a-z]+)?",  # The Midway, The Chapel
                        r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s(?:Club|Hall|Theater|Theatre|Room|Lounge|Bar|Ballroom|Arena)",
                        r"[A-Z][a-z]+\'s",  # Antone's, Yoshi's
                    ]

                    for pattern in patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            # Filter out common false positives
                            if match.lower() not in ["the city", "the best", "the top", "the most", "the new"]:
                                venue_candidates.add(match.strip())

        except Exception as e:
            continue  # Silently continue on discovery errors

    venues = list(venue_candidates)[:max_venues]

    if venues:
        print(f"   → Discovered {len(venues)} indie venues: {', '.join(venues)}")

    return venues


def _search_tavily(query: str, domains: List[str], max_results: int = 15) -> List[dict]:
    """
    Execute a single Tavily search query.

    Returns list of result dicts with 'url' and 'title' keys.
    """
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_KEY,
                "query": query,
                "include_domains": domains,
                "max_results": max_results,
                "search_depth": "advanced"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        return []


def _is_event_page(url: str) -> bool:
    """
    Check if URL is an event detail page (not a listing page).

    Event pages have specific URL patterns that indicate they're
    for a single concert, not a list of concerts.
    """
    # Check known event page patterns
    if "songkick.com/concerts/" in url:
        return True
    if "bandsintown.com/e/" in url:
        return True
    # SeatGeek event pages have long URLs with venue/date info or /concert/ suffix
    if "seatgeek.com" in url and "/concert/" in url:
        return True
    if "seatgeek.com" in url and re.search(r"/tickets/[\w-]+-\d{4}-\d{2}-\d{2}", url):
        return True

    return False


def get_concerts_tavily_enhanced(
    context: SearchContext,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    Comprehensive Tavily approach for indie/small venue concert discovery:

    1. DISCOVER indie venues dynamically for the location
    2. SEARCH day-by-day for better date coverage
    3. SEARCH venue-specific queries for discovered venues
    4. EXTRACT full content from top URLs
    5. Return raw page content for Claude to parse

    This captures small venues, indie shows, and local scenes that
    Ticketmaster often misses.

    Args:
        context: SearchContext from Context Router
        start_date: ISO date (YYYY-MM-DD)
        end_date: ISO date (YYYY-MM-DD)

    Returns:
        List of full page contents (markdown) from concert listing sites

    Example:
        >>> context = analyze_city("Austin, TX", "2025-01-10", "2025-01-17")
        >>> pages = get_concerts_tavily_enhanced(context, "2025-01-10", "2025-01-17")
        >>> len(pages)
        15
    """
    location = context.location_info.normalized_location
    city = location.split(",")[0].strip()

    # Domains to search (with event page patterns)
    search_domains = ["songkick.com", "bandsintown.com", "seatgeek.com"]

    all_urls: Set[str] = set()
    skipped_count = 0

    # =========================================================================
    # STEP 1: Discover indie venues for this location
    # =========================================================================
    print(f"   → Discovering indie venues for {city}...")
    indie_venues = discover_indie_venues(location, max_venues=5)

    # =========================================================================
    # STEP 2: Generate search queries
    # =========================================================================
    print(f"   → Building search queries...")

    # Get individual dates in range
    dates = _get_dates_in_range(start_date, end_date)

    search_queries = []

    # --- Original queries (date range based) ---
    search_queries.extend([
        f"concerts near {location} {start_date} site:songkick.com/concerts",
        f"live music near {location} {start_date} site:bandsintown.com/e",
        f"shows near {location} {start_date} to {end_date} site:songkick.com/concerts",
        f"events near {location} {start_date} site:bandsintown.com/e",
    ])

    # --- Day-by-day queries (for each date in range) ---
    for date in dates:
        friendly_date = _format_date_for_search(date)
        search_queries.extend([
            f"concerts {city} {friendly_date} site:songkick.com/concerts",
            f"live music {city} {friendly_date} site:bandsintown.com/e",
            f"concerts {city} {friendly_date} site:seatgeek.com",
        ])

    # --- Venue-specific queries (for discovered venues) ---
    for venue in indie_venues:
        search_queries.extend([
            f"{venue} {city} concerts {start_date[:7]} site:songkick.com",  # YYYY-MM
            f"{venue} concerts site:bandsintown.com/e",
            f"{venue} {city} site:seatgeek.com",
        ])

    print(f"   → Executing {len(search_queries)} search queries...")

    # =========================================================================
    # STEP 3: Execute searches and collect event URLs
    # =========================================================================
    for query in search_queries:
        results = _search_tavily(query, search_domains, max_results=10)

        for result in results:
            url = result.get("url", "")

            if _is_event_page(url):
                all_urls.add(url)
            else:
                skipped_count += 1

    if skipped_count > 0:
        print(f"   ⊗ Skipped {skipped_count} listing pages")

    if not all_urls:
        print("⚠️  Tavily SEARCH: No event detail pages found")
        return []

    print(f"   → Found {len(all_urls)} unique event pages")

    # =========================================================================
    # STEP 4: Extract full content from top URLs
    # =========================================================================
    max_extract = 15  # Extract more pages for better coverage
    top_urls = list(all_urls)[:max_extract]

    print(f"   → Extracting content from top {len(top_urls)} pages...")

    try:
        response = requests.post(
            "https://api.tavily.com/extract",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_KEY,
                "urls": top_urls,
                "format": "markdown"
            },
            timeout=45  # Longer timeout for more pages
        )
        response.raise_for_status()
        data = response.json()

        if "results" in data:
            page_contents = []
            for result in data["results"]:
                if "raw_content" in result:
                    content = f"SOURCE: {result['url']}\n\n{result['raw_content']}"
                    page_contents.append(content)

            print(f"✅ Tavily EXTRACT: Successfully extracted {len(page_contents)} pages")
            return page_contents
        else:
            print("⚠️  Tavily EXTRACT: No content extracted")
            return []

    except Exception as e:
        print(f"❌ Tavily EXTRACT error: {e}")
        return []
