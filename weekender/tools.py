"""
LangGraph Concert Agent Tools
=============================

Tools for the concert discovery agent using LangGraph.
Each tool can be called by the LLM to gather concert information.
"""

import json
import re
import requests
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from config import (
    TICKETMASTER_API_KEY,
    TAVILY_API_KEY,
    ANTHROPIC_API_KEY,
    CONCERT_DOMAINS,
    MAX_VENUES_TO_DISCOVER,
    MAX_PAGES_TO_EXTRACT,
    TICKETMASTER_RESULTS_LIMIT
)


# =============================================================================
# Tool 1: Analyze Location
# =============================================================================

@tool
def analyze_location(city: str) -> Dict[str, Any]:
    """
    Analyze a city to get geographic coordinates and search parameters.

    Use this tool FIRST to understand the location before searching.

    Args:
        city: City name (e.g., "Austin, Texas" or "San Francisco")

    Returns:
        Dictionary with latitude, longitude, and recommended search radius.
    """
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=500
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Return ONLY valid JSON with geographic info for this city.
Format:
{{
  "city": "normalized city name",
  "latitude": number,
  "longitude": number,
  "search_radius_miles": number (5-25 based on city size),
  "city_type": "large_metro" | "medium_city" | "small_area"
}}

Examples:
- Austin, TX: radius 20 (medium city)
- NYC: radius 25 (large metro)
- Palo Alto: radius 30 (small, expand search)
"""),
        ("human", "Analyze: {city}")
    ])

    try:
        response = (prompt | llm).invoke({"city": city})
        content = response.content.strip()

        # Clean JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)
    except Exception as e:
        # Fallback with reasonable defaults
        return {
            "city": city,
            "latitude": 30.2672,  # Austin default
            "longitude": -97.7431,
            "search_radius_miles": 20,
            "city_type": "medium_city",
            "error": str(e)
        }


# =============================================================================
# Tool 2: Search Ticketmaster
# =============================================================================

@tool
def search_ticketmaster(
    latitude: float,
    longitude: float,
    radius_miles: int,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Search Ticketmaster Discovery API for concerts.

    This finds mainstream concerts at larger venues.

    Args:
        latitude: Latitude of search center
        longitude: Longitude of search center
        radius_miles: Search radius in miles
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of concert objects with name, venue, date, time, url, etc.
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    params = {
        "apikey": TICKETMASTER_API_KEY,
        "classificationName": "music",
        "latlong": f"{latitude},{longitude}",
        "radius": radius_miles,
        "unit": "miles",
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "sort": "date,asc",
        "size": TICKETMASTER_RESULTS_LIMIT
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "_embedded" not in data or "events" not in data["_embedded"]:
            return []

        events = data["_embedded"]["events"]
        formatted = []

        for event in events:
            venue_info = event.get("_embedded", {}).get("venues", [{}])[0]
            city = venue_info.get("city", {}).get("name", "")
            state = venue_info.get("state", {}).get("stateCode", "")
            location = f"{city}, {state}" if city and state else city or "TBD"

            # Extract price range
            price_ranges = event.get("priceRanges", [])
            price_range = None
            if price_ranges:
                pr = price_ranges[0]
                min_p, max_p = pr.get("min"), pr.get("max")
                if min_p and max_p:
                    price_range = f"${int(min_p)}-${int(max_p)}"

            # Extract genre
            classifications = event.get("classifications", [])
            genre = classifications[0].get("genre", {}).get("name") if classifications else None

            formatted.append({
                "name": event.get("name", "Unknown"),
                "venue": venue_info.get("name", "Unknown Venue"),
                "date": event.get("dates", {}).get("start", {}).get("localDate", "TBD"),
                "time": event.get("dates", {}).get("start", {}).get("localTime"),
                "location": location,
                "price_range": price_range,
                "url": event.get("url"),
                "source": "ticketmaster",
                "genre": genre
            })

        return formatted

    except Exception as e:
        print(f"Ticketmaster error: {e}")
        return []


# =============================================================================
# Tool 3: Discover Venues
# =============================================================================

@tool
def discover_venues(city: str, max_venues: int = 5) -> List[str]:
    """
    Discover indie/small concert venues in a city.

    Use this to find local venues not typically on Ticketmaster.

    Args:
        city: City name
        max_venues: Maximum venues to return (default 5)

    Returns:
        List of venue names discovered for the city.
    """
    venue_queries = [
        f"best indie concert venues {city}",
        f"small live music venues {city}",
        f"underground music venues {city}",
        f"best EDM clubs {city}",
        f"jazz clubs {city}",
    ]

    venue_candidates: Set[str] = set()

    for query in venue_queries[:3]:  # Limit queries for speed
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
                # Extract venue patterns
                patterns = [
                    r"The [A-Z][a-z]+(?:\s[A-Z][a-z]+)?",
                    r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s(?:Club|Hall|Theater|Theatre|Room|Lounge|Bar|Ballroom)",
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if match.lower() not in ["the city", "the best", "the top"]:
                            venue_candidates.add(match.strip())
        except Exception:
            continue

    return list(venue_candidates)[:max_venues]


# =============================================================================
# Tool 4: Search Web for Concerts
# =============================================================================

def _format_date_for_search(date_str: str) -> str:
    """Format date for search queries."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d %Y").replace(" 0", " ")


def _is_event_page(url: str) -> bool:
    """Check if URL is a concert event page."""
    if "songkick.com/concerts/" in url:
        return True
    if "bandsintown.com/e/" in url:
        return True
    if "seatgeek.com" in url and "/concert/" in url:
        return True
    return False


@tool
def search_web_concerts(
    city: str,
    start_date: str,
    end_date: str,
    venues: List[str] = None
) -> List[str]:
    """
    Search web sources for concerts not on Ticketmaster.

    Searches Songkick, Bandsintown, SeatGeek for indie concerts.

    Args:
        city: City to search
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        venues: Optional list of specific venues to search

    Returns:
        List of page contents (markdown) from concert sites.
    """
    if venues is None:
        venues = []

    search_domains = list(CONCERT_DOMAINS.keys())
    all_urls: Set[str] = set()

    # Build search queries
    queries = [
        f"concerts near {city} {start_date} site:songkick.com/concerts",
        f"live music near {city} {start_date} site:bandsintown.com/e",
        f"concerts {city} {_format_date_for_search(start_date)} site:seatgeek.com",
    ]

    # Add venue-specific queries
    for venue in venues[:3]:
        queries.append(f"{venue} {city} concerts {start_date[:7]} site:songkick.com")

    # Execute searches
    for query in queries:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "include_domains": search_domains,
                    "max_results": 10,
                    "search_depth": "advanced"
                },
                timeout=15
            )
            response.raise_for_status()

            for result in response.json().get("results", []):
                url = result.get("url", "")
                if _is_event_page(url):
                    all_urls.add(url)
        except Exception:
            continue

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

        page_contents = []
        for result in response.json().get("results", []):
            if "raw_content" in result:
                content = f"SOURCE: {result['url']}\n\n{result['raw_content']}"
                page_contents.append(content)

        return page_contents

    except Exception as e:
        print(f"Tavily extract error: {e}")
        return []


# =============================================================================
# Tool 5: Aggregate and Parse Results
# =============================================================================

@tool
def aggregate_concerts(
    ticketmaster_results: List[Dict[str, Any]],
    web_page_contents: List[str],
    start_date: str,
    end_date: str,
    location: str = ""
) -> List[Dict[str, Any]]:
    """
    Aggregate and deduplicate concert results from all sources.

    Uses Claude to parse web pages and combine with Ticketmaster results.

    Args:
        ticketmaster_results: Concerts from Ticketmaster
        web_page_contents: Raw page contents from web search
        start_date: Filter start date (YYYY-MM-DD)
        end_date: Filter end date (YYYY-MM-DD)
        location: Location for context

    Returns:
        Deduplicated list of concerts sorted by date.
    """
    # Filter Ticketmaster by date
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        start_dt = end_dt = None

    filtered_tm = []
    for concert in ticketmaster_results:
        date_str = concert.get("date", "")
        if not date_str or date_str == "TBD":
            continue
        try:
            concert_dt = datetime.strptime(date_str, "%Y-%m-%d")
            if start_dt and end_dt and start_dt <= concert_dt <= end_dt:
                filtered_tm.append(concert)
        except ValueError:
            continue

    if not web_page_contents:
        return sorted(filtered_tm, key=lambda x: x.get("date", "9999-99-99"))

    # Use Claude to parse web pages
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=8000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract concerts from the web pages. Return ONLY valid JSON.

Rules:
1. Only concerts between {start_date} and {end_date}
2. For each concert: name, venue, date (YYYY-MM-DD), time, location, price_range, url, source, genre
3. If field missing, use null

Output:
{{"concerts": [{{"name": "...", "venue": "...", "date": "YYYY-MM-DD", ...}}]}}
"""),
        ("human", """Parse these pages for concerts:

{web_pages}

Date range: {start_date} to {end_date}
Location: {location}""")
    ])

    try:
        # Truncate pages aggressively to stay under token limits
        # 8 pages × 3000 chars = ~24k chars = ~30k tokens (safe margin)
        truncated = [p[:3000] for p in web_page_contents[:8]]

        response = (prompt | llm).invoke({
            "web_pages": "\n\n---\n\n".join(truncated),
            "start_date": start_date,
            "end_date": end_date,
            "location": location
        })

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Find JSON
        json_start = content.find("{")
        json_end = content.rfind("}")
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end + 1]

        data = json.loads(content)
        web_concerts = data.get("concerts", [])

    except Exception as e:
        print(f"Parse error: {e}")
        web_concerts = []

    # Combine and deduplicate
    all_concerts = filtered_tm + web_concerts

    seen = set()
    unique = []
    for concert in all_concerts:
        key = (
            (concert.get("name") or "").lower().strip(),
            (concert.get("venue") or "").lower().strip(),
            concert.get("date") or ""
        )
        if key not in seen:
            seen.add(key)
            unique.append(concert)

    return sorted(unique, key=lambda x: x.get("date", "9999-99-99"))


# =============================================================================
# All Tools List
# =============================================================================

ALL_TOOLS = [
    analyze_location,
    search_ticketmaster,
    discover_venues,
    search_web_concerts,
    aggregate_concerts,
]
