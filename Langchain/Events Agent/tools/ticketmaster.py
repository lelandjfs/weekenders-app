"""
Ticketmaster Tool for LangChain Events Agent
==============================================

LangChain-compatible tool for fetching NON-MUSIC events from Ticketmaster.
Covers: Sports, Arts & Theatre, Family, Film, Comedy, etc.
"""

import requests
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TICKETMASTER_API_KEY,
    TICKETMASTER_RESULTS_LIMIT,
    DEFAULT_SEARCH_RADIUS,
    get_city_coordinates
)


class TicketmasterEventsInput(BaseModel):
    """Input schema for Ticketmaster events search."""
    city: str = Field(description="City name to search in")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    radius_miles: int = Field(
        default=25,
        description="Search radius in miles"
    )


@tool(args_schema=TicketmasterEventsInput)
def search_ticketmaster_events(
    city: str,
    start_date: str,
    end_date: str,
    radius_miles: int = 25
) -> List[Dict]:
    """
    Search Ticketmaster for NON-MUSIC events (sports, theater, comedy, etc.)

    Args:
        city: City name (e.g., "San Francisco", "Sacramento")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        radius_miles: Search radius in miles

    Returns:
        List of event dictionaries
    """
    # Get coordinates dynamically
    coords = get_city_coordinates(city)
    if not coords:
        print(f"   ⚠️ Could not find coordinates for {city}")
        return []

    latitude, longitude = coords
    print(f"   → Searching Ticketmaster for events near {city} ({latitude}, {longitude})...")

    all_events = []
    seen_events = set()

    # Search each non-music classification
    classifications = [
        ("Sports", "KZFzniwnSyZfZ7v7nE"),
        ("Arts & Theatre", "KZFzniwnSyZfZ7v7na"),
        ("Family", "KZFzniwnSyZfZ7v7n1"),
    ]

    for class_name, class_id in classifications:
        events = _search_classification(
            latitude, longitude, radius_miles,
            start_date, end_date, class_id, class_name
        )

        for event in events:
            event_key = f"{event['name']}_{event['venue']}_{event['date']}"
            if event_key not in seen_events:
                seen_events.add(event_key)
                all_events.append(event)

    print(f"   ✅ Found {len(all_events)} events from Ticketmaster")

    return all_events


def _search_classification(
    latitude: float,
    longitude: float,
    radius_miles: int,
    start_date: str,
    end_date: str,
    classification_id: str,
    classification_name: str
) -> List[Dict]:
    """Search a specific Ticketmaster classification."""
    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    params = {
        "apikey": TICKETMASTER_API_KEY,
        "classificationId": classification_id,
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

            formatted.append({
                "name": event.get("name", "Unknown"),
                "venue": venue_info.get("name", "Unknown Venue"),
                "date": event.get("dates", {}).get("start", {}).get("localDate", "TBD"),
                "time": event.get("dates", {}).get("start", {}).get("localTime"),
                "location": _format_location(venue_info),
                "category": classification_name,
                "subcategory": _extract_subcategory(event.get("classifications", [])),
                "price_range": _extract_price_range(event.get("priceRanges", [])),
                "url": event.get("url"),
                "image": _extract_image(event.get("images", [])),
                "source": "ticketmaster"
            })

        return formatted

    except requests.RequestException as e:
        print(f"   ⚠️ Ticketmaster API error ({classification_name}): {e}")
        return []


def _format_location(venue: Dict) -> str:
    """Format venue location as 'City, State'."""
    city = venue.get("city", {}).get("name", "")
    state = venue.get("state", {}).get("stateCode", "")
    if city and state:
        return f"{city}, {state}"
    elif city:
        return city
    return "Location TBD"


def _extract_subcategory(classifications: List[Dict]) -> Optional[str]:
    """Extract subcategory from Ticketmaster classifications."""
    if not classifications:
        return None

    cls = classifications[0]

    # Try genre first, then subGenre
    genre = cls.get("genre", {}).get("name")
    if genre and genre != "Undefined":
        return genre

    subgenre = cls.get("subGenre", {}).get("name")
    if subgenre and subgenre != "Undefined":
        return subgenre

    return None


def _extract_price_range(price_ranges: List[Dict]) -> Optional[str]:
    """Extract price range from Ticketmaster data."""
    if not price_ranges:
        return None

    pr = price_ranges[0]
    min_price = pr.get("min")
    max_price = pr.get("max")

    if min_price and max_price:
        return f"${int(min_price)}-${int(max_price)}"
    elif min_price:
        return f"From ${int(min_price)}"
    return None


def _extract_image(images: List[Dict]) -> Optional[str]:
    """Extract best image from Ticketmaster images."""
    if not images:
        return None

    # Prefer larger images
    for img in sorted(images, key=lambda x: x.get("width", 0), reverse=True):
        if img.get("url"):
            return img["url"]

    return None
