"""
Web Search Tool for LangChain Events Agent
============================================

LangChain-compatible tool for searching local events from
Eventbrite, Timeout, and general web sources.
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


class WebSearchEventsInput(BaseModel):
    """Input schema for web events search."""
    city: str = Field(description="City name to search for")
    start_date: str = Field(description="Start date for context")
    end_date: str = Field(description="End date for context")


@tool(args_schema=WebSearchEventsInput)
@traceable(name="tavily_web_events_api", run_type="tool")
def search_web_events(
    city: str,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    Search web sources for local events (Eventbrite, Timeout, etc.)

    Args:
        city: City name (e.g., "San Francisco")
        start_date: Start date for search context
        end_date: End date for search context

    Returns:
        List of extracted page contents (markdown)
    """
    all_urls: Set[str] = set()

    print(f"   → Searching web sources for {city} events...")

    # Search each source
    for source_name, source_config in WEB_SEARCH_SOURCES.items():
        domain = source_config["domain"]
        queries = source_config["queries"]

        print(f"   → Searching {source_name}...")

        for query_template in queries:
            query = query_template.format(city=city)

            # Add date context for time-sensitive searches
            if "this weekend" not in query.lower():
                query = f"{query} {start_date}"

            if domain:
                urls = _search_tavily(query, [domain], MAX_WEB_RESULTS_PER_SOURCE)
            else:
                urls = _search_tavily(query, [], MAX_WEB_RESULTS_PER_SOURCE)

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
            if url and _is_valid_event_url(url):
                urls.add(url)

        return urls

    except Exception as e:
        print(f"   ⚠️ Search error: {e}")
        return set()


def _is_valid_event_url(url: str) -> bool:
    """Filter out non-event URLs."""
    skip_patterns = [
        "/search",
        "/category",
        "/tag",
        "/author",
        "/login",
        "/signup",
        "/cart",
    ]

    for pattern in skip_patterns:
        if pattern in url.lower():
            return False

    # Eventbrite event pages have /e/ in URL
    if "eventbrite.com" in url:
        return "/e/" in url or "/d/" in url

    # Timeout articles
    if "timeout.com" in url:
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
                content = f"SOURCE: {url}\n\n{raw_content}"
                page_contents.append(content)

        return page_contents

    except Exception as e:
        print(f"   ⚠️ Extraction error: {e}")
        return []
