"""
Google Places Tool
===================

Searches Google Places API for highly-rated restaurants.
Focuses on restaurants with high ratings and many reviews.
"""

import requests
from typing import List, Dict, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GOOGLE_PLACES_KEY,
    GOOGLE_PLACES_FIELDS,
    MIN_RATING,
    MIN_REVIEWS,
    MAX_RESULTS_PER_NEIGHBORHOOD
)


def search_google_places(
    city: str,
    neighborhoods: List[str] = None,
    cuisine_type: str = None,
    min_rating: float = None,
    min_reviews: int = None,
    max_results: int = None
) -> List[Dict[str, Any]]:
    """
    Search Google Places for highly-rated restaurants.

    Args:
        city: City name (e.g., "San Francisco")
        neighborhoods: List of neighborhoods to search (optional)
        cuisine_type: Specific cuisine to search for (optional)
        min_rating: Minimum rating filter (default: 4.0)
        min_reviews: Minimum review count (default: 50)
        max_results: Max results per query (default: 10)

    Returns:
        List of restaurant dictionaries with details
    """
    if min_rating is None:
        min_rating = MIN_RATING
    if min_reviews is None:
        min_reviews = MIN_REVIEWS
    if max_results is None:
        max_results = MAX_RESULTS_PER_NEIGHBORHOOD

    all_restaurants = []
    seen_places = set()  # For deduplication

    # Build search queries
    queries = []

    if neighborhoods:
        for hood in neighborhoods:
            if cuisine_type:
                queries.append(f"best {cuisine_type} restaurants in {hood}, {city}")
            else:
                queries.append(f"best restaurants in {hood}, {city}")
    else:
        # City-wide search
        if cuisine_type:
            queries.append(f"best {cuisine_type} restaurants in {city}")
        else:
            queries.append(f"best restaurants in {city}")
            queries.append(f"highly rated restaurants in {city}")
            queries.append(f"popular restaurants in {city}")

    print(f"   → Searching Google Places ({len(queries)} queries)...")

    for query in queries:
        results = _search_places_text(query, max_results)

        for place in results:
            # Get place ID for deduplication
            place_id = place.get("id") or place.get("displayName", {}).get("text", "")

            if place_id in seen_places:
                continue

            # Filter by rating and reviews
            rating = place.get("rating", 0)
            review_count = place.get("userRatingCount", 0)

            if rating >= min_rating and review_count >= min_reviews:
                seen_places.add(place_id)
                formatted = _format_place(place, query)
                all_restaurants.append(formatted)

    print(f"   ✅ Found {len(all_restaurants)} restaurants from Google Places")

    return all_restaurants


def _search_places_text(query: str, max_results: int = 10) -> List[Dict]:
    """
    Execute a text search query against Google Places API.
    """
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

    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])

    except requests.RequestException as e:
        print(f"   ⚠️ Google Places error: {e}")
        return []


def _format_place(place: Dict, query: str) -> Dict[str, Any]:
    """
    Format a Google Places result into our standard structure.
    """
    display_name = place.get("displayName", {})
    name = display_name.get("text", "Unknown")

    # Extract price level
    price_level = place.get("priceLevel")
    price_str = _format_price_level(price_level)

    # Extract neighborhood from query or address
    address = place.get("formattedAddress", "")
    neighborhood = _extract_neighborhood_from_address(address)

    # Get opening hours
    hours = place.get("regularOpeningHours", {})
    open_now = hours.get("openNow")

    return {
        "name": name,
        "address": address,
        "neighborhood": neighborhood,
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount"),
        "price_level": price_str,
        "cuisine_type": _extract_cuisine(place.get("types", []), place.get("primaryType")),
        "website": place.get("websiteUri"),
        "google_maps_url": place.get("googleMapsUri"),
        "open_now": open_now,
        "source": "google_places"
    }


def _format_price_level(price_level: str) -> Optional[str]:
    """Convert Google's price level to $ symbols."""
    if not price_level:
        return None

    price_map = {
        "PRICE_LEVEL_FREE": "Free",
        "PRICE_LEVEL_INEXPENSIVE": "$",
        "PRICE_LEVEL_MODERATE": "$$",
        "PRICE_LEVEL_EXPENSIVE": "$$$",
        "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
    }

    return price_map.get(price_level, price_level)


def _extract_neighborhood_from_address(address: str) -> Optional[str]:
    """
    Try to extract neighborhood from address.
    Usually the second component before city.
    """
    if not address:
        return None

    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        # Often format is: Street, Neighborhood, City, State ZIP
        return parts[1]

    return None


def _extract_cuisine(types: List[str], primary_type: str = None) -> Optional[str]:
    """
    Extract cuisine type from Google Places types.
    """
    # Map Google types to cuisine names
    cuisine_map = {
        "mexican_restaurant": "Mexican",
        "italian_restaurant": "Italian",
        "japanese_restaurant": "Japanese",
        "chinese_restaurant": "Chinese",
        "thai_restaurant": "Thai",
        "indian_restaurant": "Indian",
        "vietnamese_restaurant": "Vietnamese",
        "korean_restaurant": "Korean",
        "french_restaurant": "French",
        "american_restaurant": "American",
        "seafood_restaurant": "Seafood",
        "steak_house": "Steakhouse",
        "pizza_restaurant": "Pizza",
        "sushi_restaurant": "Sushi",
        "ramen_restaurant": "Ramen",
        "barbecue_restaurant": "BBQ",
        "brunch_restaurant": "Brunch",
        "breakfast_restaurant": "Breakfast",
        "cafe": "Cafe",
        "coffee_shop": "Coffee",
        "bakery": "Bakery",
        "bar": "Bar",
        "wine_bar": "Wine Bar",
    }

    # Check primary type first
    if primary_type and primary_type in cuisine_map:
        return cuisine_map[primary_type]

    # Check all types
    for t in types:
        if t in cuisine_map:
            return cuisine_map[t]

    return None
