"""
Web Search Tool for Restaurants
=================================

Searches curated restaurant sources:
- Eater (city guides, best-of lists)
- The Infatuation (curated reviews)
- Reddit (local recommendations)

Uses Tavily for search and extraction.
"""

import requests
from typing import List, Set

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TAVILY_API_KEY,
    WEB_SEARCH_SOURCES,
    MAX_WEB_RESULTS_PER_SOURCE,
    MAX_PAGES_TO_EXTRACT
)


def search_web_restaurants(
    city: str,
    neighborhoods: List[str] = None
) -> List[str]:
    """
    Search curated web sources for restaurant recommendations.

    Searches Eater, The Infatuation, and Reddit for best restaurant
    lists and recommendations, then extracts page content.

    Args:
        city: City name (e.g., "San Francisco")
        neighborhoods: Optional list of neighborhoods to include

    Returns:
        List of extracted page contents (markdown)
    """
    all_urls: Set[str] = set()

    print(f"   → Searching web sources for {city} restaurants...")

    # Search each source
    for source_name, source_config in WEB_SEARCH_SOURCES.items():
        domain = source_config["domain"]
        queries = source_config["queries"]

        print(f"   → Searching {source_name}...")

        for query_template in queries:
            query = query_template.format(city=city)
            urls = _search_tavily(query, [domain], MAX_WEB_RESULTS_PER_SOURCE)
            all_urls.update(urls)

        # Also search neighborhoods if provided
        if neighborhoods:
            for hood in neighborhoods[:3]:  # Limit to top 3 neighborhoods
                query = f"best restaurants {hood} {city} site:{domain}"
                urls = _search_tavily(query, [domain], 5)
                all_urls.update(urls)

    print(f"   → Found {len(all_urls)} unique URLs")

    if not all_urls:
        return []

    # Extract content from top URLs
    top_urls = list(all_urls)[:MAX_PAGES_TO_EXTRACT]
    print(f"   → Extracting content from {len(top_urls)} pages...")

    page_contents = _extract_pages(top_urls)

    print(f"   ✅ Extracted {len(page_contents)} pages from web sources")

    return page_contents


def _search_tavily(query: str, domains: List[str], max_results: int) -> Set[str]:
    """
    Execute a Tavily search and return URLs.
    """
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
        data = response.json()

        urls = set()
        for result in data.get("results", []):
            url = result.get("url", "")
            if url and _is_valid_article_url(url):
                urls.add(url)

        return urls

    except Exception as e:
        print(f"   ⚠️ Search error: {e}")
        return set()


def _is_valid_article_url(url: str) -> bool:
    """
    Filter out non-article URLs (homepages, search pages, etc.)
    """
    # Skip homepage and generic pages
    skip_patterns = [
        "/search",
        "/category",
        "/tag",
        "/author",
        "/page/",
        "/?",
    ]

    for pattern in skip_patterns:
        if pattern in url:
            return False

    # Eater article URLs usually have city + article slug
    if "eater.com" in url:
        # Valid Eater URLs: eater.com/city/... or eater.com/maps/...
        return "/maps/" in url or url.count("/") >= 4

    # Infatuation URLs: theinfatuation.com/city/...
    if "theinfatuation.com" in url:
        return url.count("/") >= 4

    # Reddit URLs: reddit.com/r/... with comments
    if "reddit.com" in url:
        return "/comments/" in url or "/r/" in url

    return True


def _extract_pages(urls: List[str]) -> List[str]:
    """
    Extract full page content from URLs using Tavily.
    """
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
                content = f"SOURCE: {url}\n\n{raw_content}"
                page_contents.append(content)

        return page_contents

    except Exception as e:
        print(f"   ⚠️ Extraction error: {e}")
        return []
