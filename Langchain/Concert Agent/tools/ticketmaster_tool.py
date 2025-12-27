"""
Ticketmaster Tool
=================

Fetches concert data from Ticketmaster Discovery API.

This tool:
- Uses context-driven parameters (lat/long, radius from Context Router)
- Returns structured concert data (big venues, mainstream concerts)
- Operates independently for LangSmith tracing
"""

import requests
from typing import List, Dict, Optional
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context_router import SearchContext

# API Key
TICKETMASTER_KEY = "wtwlR1qylRp6pwQwTbMHmAFqQG8B1zRl"


def get_concerts_ticketmaster(
    context: SearchContext,
    start_date: str,
    end_date: str
) -> List[Dict]:
    """
    Get concerts from Ticketmaster API using context parameters.

    CONTEXT-DRIVEN: Uses lat/long and radius from Context Router.

    Args:
        context: SearchContext from Context Router
        start_date: ISO date (YYYY-MM-DD)
        end_date: ISO date (YYYY-MM-DD)

    Returns:
        List of formatted concert data from Ticketmaster

    Example:
        >>> context = analyze_city("Austin, TX", "2025-01-10", "2025-01-17")
        >>> concerts = get_concerts_ticketmaster(context, "2025-01-10", "2025-01-17")
        >>> len(concerts)
        42
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    # ALL PARAMETERS COME FROM CONTEXT ROUTER - NO HARDCODING
    params = {
        "apikey": TICKETMASTER_KEY,
        "classificationName": "music",  # CONCERTS ONLY (not sports/theater)
        "latlong": f"{context.location_info.latitude},{context.location_info.longitude}",
        "radius": int(context.search_parameters.concert_radius_miles),  # ← FROM CONTEXT
        "unit": "miles",
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "sort": "date,asc",
        "size": 50  # Get up to 50 concerts
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "_embedded" in data and "events" in data["_embedded"]:
            events = data["_embedded"]["events"]

            # Format for aggregation
            formatted = []
            for event in events:
                formatted.append({
                    "name": event.get("name", "Unknown"),
                    "venue": event.get("_embedded", {}).get("venues", [{}])[0].get("name", "Unknown Venue"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate", "TBD"),
                    "time": event.get("dates", {}).get("start", {}).get("localTime"),
                    "location": _format_location(event.get("_embedded", {}).get("venues", [{}])[0]),
                    "price_range": _extract_price_range(event.get("priceRanges", [])),
                    "url": event.get("url"),
                    "source": "ticketmaster",
                    "genre": _extract_genre(event.get("classifications", []))
                })

            print(f"✅ Ticketmaster: Found {len(formatted)} concerts")
            return formatted
        else:
            print("⚠️  Ticketmaster: No concerts found")
            return []

    except Exception as e:
        print(f"❌ Ticketmaster error: {e}")
        return []


# Helper functions

def _format_location(venue: Dict) -> str:
    """Format venue location as 'City, State'"""
    city = venue.get("city", {}).get("name", "")
    state = venue.get("state", {}).get("stateCode", "")
    if city and state:
        return f"{city}, {state}"
    elif city:
        return city
    else:
        return "Location TBD"


def _extract_price_range(price_ranges: List[Dict]) -> Optional[str]:
    """Extract price range from Ticketmaster data"""
    if not price_ranges:
        return None

    pr = price_ranges[0]
    min_price = pr.get("min")
    max_price = pr.get("max")

    if min_price and max_price:
        return f"${int(min_price)}-${int(max_price)}"
    elif min_price:
        return f"From ${int(min_price)}"
    else:
        return None


def _extract_genre(classifications: List[Dict]) -> Optional[str]:
    """Extract genre from Ticketmaster classifications"""
    if not classifications:
        return None

    genre = classifications[0].get("genre", {}).get("name")
    return genre
