"""
Parallel AI Web Search Module
==============================

Replaces Tavily for fast web search with pre-structured results.
Uses Parallel AI REST API for 7-11x faster searches.

Benefits:
- 4-5 second searches vs 30-55 seconds with Tavily
- Pre-structured excerpts (reduces Haiku parsing needs)
- 9-10 quality sources per search
- Source attribution included
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Parallel AI API configuration
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")
PARALLEL_SEARCH_URL = "https://api.parallel.ai/v1beta/search"


def search_web(
    objective: str,
    search_queries: List[str],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Execute a Parallel AI web search.

    Args:
        objective: Natural language description of what to find
        search_queries: List of keyword search queries (1-6 words each)
        max_results: Maximum number of results (default 10)

    Returns:
        Dict with 'results' list containing structured excerpts
    """
    if not PARALLEL_API_KEY:
        print("   Warning: PARALLEL_API_KEY not set")
        return {"results": [], "error": "API key not configured"}

    try:
        payload = {
            "objective": objective,
            "search_queries": search_queries[:5],  # Parallel limits to 5 queries
            "max_results": max_results,
            "excerpts": {
                "max_chars_per_result": 10000
            }
        }

        response = requests.post(
            PARALLEL_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": PARALLEL_API_KEY,
                "parallel-beta": "search-extract-2025-10-10"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        return data

    except Exception as e:
        print(f"   Warning: Parallel search error: {e}")
        return {"results": [], "error": str(e)}


def search_restaurants(city: str, neighborhoods: List[str] = None) -> List[Dict[str, Any]]:
    """
    Search for restaurant recommendations.

    Returns list of structured results with:
    - title, url, excerpts, source
    """
    neighborhoods = neighborhoods or []
    hood_str = f" in {', '.join(neighborhoods[:3])}" if neighborhoods else ""

    objective = f"Find the best restaurants in {city}{hood_str} - hidden gems, local favorites, new openings, best dining experiences. Focus on quality restaurants that locals recommend."

    queries = [
        f"best restaurants {city} 2025",
        f"hidden gem restaurants {city} locals",
        f"new restaurant openings {city}",
        f"best dining {city} Eater"
    ]

    result = search_web(objective, queries)
    return _format_results(result, "restaurants")


def search_events(city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Search for local events.

    Returns list of structured results with event info.
    """
    objective = f"Find events, festivals, and things to do in {city} between {start_date} and {end_date}. Focus on local events, festivals, art shows, family activities."

    queries = [
        f"events {city} {start_date} weekend",
        f"things to do {city} this weekend",
        f"festivals {city} {start_date[:7]}",
        f"local events {city} Eventbrite"
    ]

    result = search_web(objective, queries)
    return _format_results(result, "events")


def search_locations(city: str) -> List[Dict[str, Any]]:
    """
    Search for hidden gems and local attractions.

    Returns list of structured results with location info.
    """
    objective = f"Find interesting things to do, attractions, and hidden gems in {city} - local favorites, unique spots, must-see places that tourists miss."

    queries = [
        f"hidden gems {city} locals only",
        f"best things to do {city} 2025",
        f"unique attractions {city}",
        f"{city} off beaten path"
    ]

    result = search_web(objective, queries)
    return _format_results(result, "locations")


def search_concerts(city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Search for concerts and live music.

    Returns list of structured results with concert info.
    """
    objective = f"Find concerts, live music, and shows in {city} between {start_date} and {end_date}. Include indie venues, local bands, and major concerts."

    queries = [
        f"concerts {city} {start_date} site:songkick.com",
        f"live music {city} {start_date[:7]}",
        f"shows {city} bandsintown",
        f"concerts {city} this weekend"
    ]

    result = search_web(objective, queries)
    return _format_results(result, "concerts")


def _format_results(result: Dict[str, Any], result_type: str) -> List[Dict[str, Any]]:
    """
    Format Parallel AI results into structured output.

    Each result contains:
    - url: Source URL
    - title: Page title
    - source: Identified source (eater, reddit, timeout, etc.)
    - excerpts: List of relevant content excerpts
    - publish_date: Date if available
    """
    formatted = []

    for item in result.get("results", []):
        url = item.get("url", "")
        source = _identify_source(url)

        formatted.append({
            "url": url,
            "title": item.get("title", ""),
            "source": source,
            "excerpts": item.get("excerpts", []),
            "publish_date": item.get("publish_date"),
            "type": result_type
        })

    return formatted


def _identify_source(url: str) -> str:
    """Identify the source type from URL."""
    url_lower = url.lower()

    source_patterns = {
        "eater": "eater.com",
        "reddit": "reddit.com",
        "timeout": "timeout.com",
        "eventbrite": "eventbrite.com",
        "yelp": "yelp.com",
        "tripadvisor": "tripadvisor.com",
        "atlas_obscura": "atlasobscura.com",
        "songkick": "songkick.com",
        "bandsintown": "bandsintown.com",
        "seatgeek": "seatgeek.com",
        "infatuation": "theinfatuation.com",
        "conde_nast": "cntraveler.com",
        "travel_leisure": "travelandleisure.com",
    }

    for source_name, domain in source_patterns.items():
        if domain in url_lower:
            return source_name

    return "web"


def get_page_contents(results: List[Dict[str, Any]]) -> List[str]:
    """
    Convert Parallel results to page content format for aggregation.

    This maintains compatibility with existing aggregation tools
    that expect raw page content strings.
    """
    page_contents = []

    for result in results:
        source = result.get("source", "web")
        url = result.get("url", "")
        title = result.get("title", "")
        excerpts = result.get("excerpts", [])

        # Build content string from excerpts
        content_parts = [
            f"SOURCE: {source}",
            f"URL: {url}",
            f"TITLE: {title}",
            ""
        ]

        for excerpt in excerpts:
            content_parts.append(excerpt)
            content_parts.append("")

        page_contents.append("\n".join(content_parts))

    return page_contents
