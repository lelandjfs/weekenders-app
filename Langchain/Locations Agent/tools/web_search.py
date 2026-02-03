"""
Web Search Tool for LangChain Locations Agent
===============================================

LangChain-compatible tool for searching hidden gems and local attractions
from Reddit, Timeout, Atlas Obscura, and travel sites.

Focused on younger, local tourist vibes - not generic tourist trap lists.
"""

import requests
from typing import List, Set
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langsmith import traceable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TAVILY_API_KEY,
    WEB_SEARCH_SOURCES,
    MAX_WEB_RESULTS_PER_SOURCE,
    MAX_PAGES_TO_EXTRACT
)


class WebSearchLocationsInput(BaseModel):
    """Input schema for web locations search."""
    city: str = Field(description="City name to search for")


@tool(args_schema=WebSearchLocationsInput)
@traceable(name="tavily_web_locations_api", run_type="tool")
def search_web_locations(city: str) -> List[str]:
    """
    Search web sources for hidden gems and local attractions.

    Sources prioritized for authentic, local tourist experience:
    - Reddit: Local subreddits for insider recommendations
    - Timeout: Curated city guides
    - Atlas Obscura: Unusual and hidden spots
    - Conde Nast Traveler: Quality travel recommendations
    - Travel + Leisure: Popular attractions

    Args:
        city: City name (e.g., "San Francisco", "Austin")

    Returns:
        List of extracted page contents (markdown)
    """
    all_urls: Set[str] = set()

    print(f"   -> Searching web sources for {city} locations...")

    # Search each source
    for source_name, source_config in WEB_SEARCH_SOURCES.items():
        domain = source_config["domain"]
        queries = source_config["queries"]

        print(f"   -> Searching {source_name}...")

        for query_template in queries:
            query = query_template.format(city=city)

            if domain:
                urls = _search_tavily(query, [domain], MAX_WEB_RESULTS_PER_SOURCE)
            else:
                urls = _search_tavily(query, [], MAX_WEB_RESULTS_PER_SOURCE)

            all_urls.update(urls)

    print(f"   -> Found {len(all_urls)} unique URLs")

    if not all_urls:
        return []

    # Extract content from top URLs
    top_urls = list(all_urls)[:MAX_PAGES_TO_EXTRACT]
    print(f"   -> Extracting content from {len(top_urls)} pages...")

    page_contents = _extract_pages(top_urls)

    print(f"   Extracted {len(page_contents)} pages from web sources")

    return page_contents


def _search_tavily(query: str, domains: List[str], max_results: int) -> Set[str]:
    """Execute a Tavily search and return URLs."""
    try:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced"
        }

        if domains:
            payload["include_domains"] = domains

        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        urls = set()
        for result in data.get("results", []):
            url = result.get("url", "")
            if url and _is_valid_location_url(url):
                urls.add(url)

        return urls

    except Exception as e:
        print(f"   Warning: Search error: {e}")
        return set()


def _is_valid_location_url(url: str) -> bool:
    """Filter out non-content URLs."""
    skip_patterns = [
        "/search",
        "/category",
        "/tag",
        "/author",
        "/login",
        "/signup",
        "/cart",
        "/checkout",
        "/account",
        "/newsletter",
        "/subscribe",
    ]

    for pattern in skip_patterns:
        if pattern in url.lower():
            return False

    # Reddit posts (good) vs Reddit listing pages (bad)
    if "reddit.com" in url:
        # We want actual post pages, not listing pages
        return "/comments/" in url or url.count("/") >= 5

    # Atlas Obscura place pages
    if "atlasobscura.com" in url:
        return "/places/" in url or "/articles/" in url

    # Timeout articles
    if "timeout.com" in url:
        return url.count("/") >= 4

    # Travel sites - article pages
    if "cntraveler.com" in url or "travelandleisure.com" in url:
        return url.count("/") >= 4

    return True


def _extract_pages(urls: List[str]) -> List[str]:
    """Extract full page content from URLs using Tavily."""
    if not urls:
        return []

    try:
        response = requests.post(
            "https://api.tavily.com/extract",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "urls": urls,
                "format": "markdown"
            },
            timeout=45
        )
        response.raise_for_status()
        data = response.json()

        page_contents = []
        for result in data.get("results", []):
            raw_content = result.get("raw_content", "")
            if raw_content:
                url = result.get("url", "")
                # Tag with source type for better context
                source_type = _identify_source(url)
                content = f"SOURCE: {source_type}\nURL: {url}\n\n{raw_content}"
                page_contents.append(content)

        return page_contents

    except Exception as e:
        print(f"   Warning: Extraction error: {e}")
        return []


def _identify_source(url: str) -> str:
    """Identify the source type from URL for tagging."""
    url_lower = url.lower()

    if "reddit.com" in url_lower:
        return "reddit"
    elif "atlasobscura.com" in url_lower:
        return "atlas_obscura"
    elif "timeout.com" in url_lower:
        return "timeout"
    elif "cntraveler.com" in url_lower:
        return "conde_nast"
    elif "travelandleisure.com" in url_lower:
        return "travel_leisure"
    else:
        return "web"
