"""
Ticketmaster Tool for LangChain
================================

LangChain-compatible tool for fetching concerts from Ticketmaster API.
Uses @tool decorator for LangSmith tracing.
"""

import requests
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TICKETMASTER_API_KEY, TICKETMASTER_RESULTS_LIMIT


class TicketmasterInput(BaseModel):
    """Input schema for Ticketmaster search."""
    latitude: float = Field(description="Latitude of the search location")
    longitude: float = Field(description="Longitude of the search location")
    radius_miles: int = Field(description="Search radius in miles")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")


@tool(args_schema=TicketmasterInput)
def search_ticketmaster(
    latitude: float,
    longitude: float,
    radius_miles: int,
    start_date: str,
    end_date: str
) -> List[Dict]:
    """
    Search Ticketmaster Discovery API for concerts in a location.

    Returns a list of concert objects with artist, venue, date, and ticket info.
    This tool focuses on mainstream venues and larger concerts.

    Args:
        latitude: Latitude of the search center
        longitude: Longitude of the search center
        radius_miles: Search radius in miles
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of concert dictionaries with keys:
        - name: Event/artist name
        - venue: Venue name
        - date: Event date (YYYY-MM-DD)
        - time: Event time (HH:MM:SS)
        - location: City, State
        - price_range: Ticket price range (if available)
        - url: Ticket purchase URL
        - source: "ticketmaster"
        - genre: Music genre
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

            formatted.append({
                "name": event.get("name", "Unknown"),
                "venue": venue_info.get("name", "Unknown Venue"),
                "date": event.get("dates", {}).get("start", {}).get("localDate", "TBD"),
                "time": event.get("dates", {}).get("start", {}).get("localTime"),
                "location": _format_location(venue_info),
                "price_range": _extract_price_range(event.get("priceRanges", [])),
                "url": event.get("url"),
                "source": "ticketmaster",
                "genre": _extract_genre(event.get("classifications", []))
            })

        return formatted

    except requests.RequestException as e:
        print(f"Ticketmaster API error: {e}")
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


def _extract_genre(classifications: List[Dict]) -> Optional[str]:
    """Extract genre from Ticketmaster classifications."""
    if not classifications:
        return None
    return classifications[0].get("genre", {}).get("name")
