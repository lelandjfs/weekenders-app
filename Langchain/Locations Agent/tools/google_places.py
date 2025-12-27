"""
Google Places Tool for LangChain Locations Agent
==================================================

LangChain-compatible tool for searching attractions via Google Places API.
Focused on non-date-specific locations: museums, parks, landmarks, hidden gems.
"""

import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GOOGLE_PLACES_KEY,
    GOOGLE_PLACES_FIELDS,
    ATTRACTION_TYPES,
    ATTRACTION_CATEGORIES,
    MIN_RATING,
    MIN_REVIEWS,
    MAX_RESULTS_PER_TYPE,
    DEFAULT_SEARCH_RADIUS,
    get_city_coordinates
)


class GooglePlacesAttractionsInput(BaseModel):
    """Input schema for Google Places attractions search."""
    city: str = Field(description="City name to search in")
    attraction_types: List[str] = Field(
        default=[],
        description="Optional list of specific attraction types to search"
    )


@tool(args_schema=GooglePlacesAttractionsInput)
def search_google_places_attractions(
    city: str,
    attraction_types: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Google Places for attractions and points of interest.

    Args:
        city: City name (e.g., "San Francisco", "Austin")
        attraction_types: Optional list of specific types to search

    Returns:
        List of attraction dictionaries with details
    """
    all_attractions = []
    seen_places = set()

    # Get city coordinates for location-biased search
    coords = get_city_coordinates(city)
    if coords:
        print(f"   → Got coordinates for {city}: {coords}")

    # Build search queries for different attraction categories
    types_to_search = attraction_types if attraction_types else ATTRACTION_TYPES

    # Group into logical search queries for efficiency
    search_queries = [
        f"museums and art galleries in {city}",
        f"parks and gardens in {city}",
        f"tourist attractions in {city}",
        f"landmarks in {city}",
        f"hidden gems in {city}",
        f"unique places to visit in {city}",
        f"popular attractions in {city}",
        f"outdoor activities in {city}",
    ]

    print(f"   → Searching Google Places ({len(search_queries)} queries)...")

    for query in search_queries:
        results = _search_places_text(query, MAX_RESULTS_PER_TYPE, coords)

        for place in results:
            # Get place ID for deduplication
            place_id = place.get("id") or place.get("displayName", {}).get("text", "")

            if place_id in seen_places:
                continue

            # Filter by rating and reviews (more lenient for attractions)
            rating = place.get("rating", 0)
            review_count = place.get("userRatingCount", 0)

            if rating >= MIN_RATING and review_count >= MIN_REVIEWS:
                seen_places.add(place_id)
                formatted = _format_attraction(place, city)
                all_attractions.append(formatted)

    print(f"   Found {len(all_attractions)} attractions from Google Places")

    return all_attractions


def _search_places_text(
    query: str,
    max_results: int = 10,
    coords: tuple = None
) -> List[Dict]:
    """Execute a text search query against Google Places API."""
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
        "X-Goog-FieldMask": ",".join(GOOGLE_PLACES_FIELDS)
    }

    body = {
        "textQuery": query,
        "maxResultCount": max_results,
        "languageCode": "en"
    }

    # Add location bias if we have coordinates
    if coords:
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": coords[0],
                    "longitude": coords[1]
                },
                "radius": DEFAULT_SEARCH_RADIUS
            }
        }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])

    except requests.RequestException as e:
        print(f"   Warning: Google Places error for '{query}': {e}")
        return []


def _format_attraction(place: Dict, city: str) -> Dict[str, Any]:
    """Format a Google Places result into our standard structure."""
    display_name = place.get("displayName", {})
    name = display_name.get("text", "Unknown")

    # Get address
    address = place.get("formattedAddress", "")

    # Get opening hours
    hours = place.get("regularOpeningHours", {})
    open_now = hours.get("openNow")
    weekday_text = hours.get("weekdayDescriptions", [])

    # Get editorial summary if available
    summary = place.get("editorialSummary", {})
    description = summary.get("text") if summary else None

    # Categorize the attraction
    types = place.get("types", [])
    primary_type = place.get("primaryType")
    category = _categorize_attraction(types, primary_type)

    # Get first photo URL if available
    photos = place.get("photos", [])
    photo_url = None
    if photos:
        # Google Places photo reference - would need additional API call to get actual URL
        photo_url = f"https://places.googleapis.com/v1/{photos[0].get('name')}/media"

    return {
        "name": name,
        "address": address,
        "city": city,
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount"),
        "category": category,
        "type": _format_type(primary_type),
        "description": description,
        "website": place.get("websiteUri"),
        "google_maps_url": place.get("googleMapsUri"),
        "open_now": open_now,
        "hours": weekday_text[:3] if weekday_text else None,  # First 3 days
        "photo_url": photo_url,
        "source": "google_places"
    }


def _categorize_attraction(types: List[str], primary_type: str = None) -> str:
    """Categorize an attraction based on its Google Places types."""
    all_types = types + ([primary_type] if primary_type else [])

    for category, type_list in ATTRACTION_CATEGORIES.items():
        for t in all_types:
            if t in type_list:
                return category

    # Default categorization based on common types
    if any(t in all_types for t in ["museum", "art_gallery"]):
        return "Museums & Art"
    elif any(t in all_types for t in ["park", "garden", "hiking"]):
        return "Nature & Parks"
    elif any(t in all_types for t in ["zoo", "aquarium"]):
        return "Wildlife"
    elif any(t in all_types for t in ["landmark", "monument", "historical"]):
        return "Landmarks"
    elif any(t in all_types for t in ["amusement", "theater", "entertainment"]):
        return "Entertainment"

    return "Attractions"


def _format_type(primary_type: str) -> Optional[str]:
    """Format the primary type into a readable string."""
    if not primary_type:
        return None

    type_map = {
        "tourist_attraction": "Tourist Attraction",
        "museum": "Museum",
        "art_gallery": "Art Gallery",
        "park": "Park",
        "hiking_area": "Hiking",
        "botanical_garden": "Botanical Garden",
        "zoo": "Zoo",
        "aquarium": "Aquarium",
        "amusement_park": "Amusement Park",
        "landmark": "Landmark",
        "historical_landmark": "Historical Landmark",
        "cultural_center": "Cultural Center",
        "performing_arts_theater": "Theater",
        "observation_deck": "Observation Deck",
        "marina": "Marina",
        "beach": "Beach",
        "national_park": "National Park",
        "state_park": "State Park",
        "city_hall": "City Hall",
        "library": "Library",
    }

    return type_map.get(primary_type, primary_type.replace("_", " ").title())
