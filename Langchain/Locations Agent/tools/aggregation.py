"""
Aggregation Tool for LangChain Locations Agent
================================================

LangChain-compatible tool for aggregating and deduplicating location results.
Uses Claude Haiku to parse web pages and combine with Google Places data.

Focuses on extracting hidden gems and authentic local recommendations.
"""

import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY


class AggregationInput(BaseModel):
    """Input schema for location aggregation."""
    google_places_results: List[Dict[str, Any]] = Field(
        description="Structured results from Google Places"
    )
    web_page_contents: List[str] = Field(
        description="Raw page contents from web search"
    )
    city: str = Field(description="City name for context")


@tool(args_schema=AggregationInput)
@traceable(name="aggregate_locations_llm", run_type="chain")
def aggregate_locations(
    google_places_results: List[Dict[str, Any]],
    web_page_contents: List[str],
    city: str
) -> List[Dict[str, Any]]:
    """
    Aggregate location results from multiple sources.

    Uses Claude Haiku to parse web pages for hidden gems and local
    recommendations, then combines with Google Places results and deduplicates.

    Args:
        google_places_results: Structured results from Google Places
        web_page_contents: Raw page contents from web search
        city: City name for context

    Returns:
        Deduplicated, categorized list of locations
    """
    all_locations = []

    # Add Google Places results directly (already structured)
    for loc in google_places_results:
        loc["source"] = "google_places"
        all_locations.append(loc)

    print(f"   -> Starting with {len(google_places_results)} Google Places locations")

    # Parse web pages with Claude Haiku
    if web_page_contents:
        web_locations = _parse_web_pages(web_page_contents, city)
        all_locations.extend(web_locations)
        print(f"   -> Added {len(web_locations)} locations from web sources")

    # Deduplicate
    unique_locations = _deduplicate(all_locations)
    print(f"   -> After deduplication: {len(unique_locations)} unique locations")

    # Sort by rating (if available), then by name
    unique_locations.sort(
        key=lambda x: (-(x.get("rating") or 0), x.get("name", "").lower())
    )

    return unique_locations


def _parse_web_pages(web_pages: List[str], city: str) -> List[Dict[str, Any]]:
    """Use Claude Haiku to parse location details from web pages."""
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=8000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a location extraction engine focused on finding hidden gems and authentic local spots.

Extract location/attraction information from the web page content provided.

PRIORITY: Focus on unique, interesting places that locals love - NOT generic tourist traps.

Rules:
1. Extract EVERY specific place/location mentioned (museums, parks, viewpoints, neighborhoods, shops, etc.)
2. For each location, extract:
   - name: place name (REQUIRED)
   - address: full address or null
   - neighborhood: neighborhood/area name or null
   - category: type (Museums & Art, Nature & Parks, Hidden Gems, Landmarks, Food & Drink, Shopping, Neighborhoods, Activities)
   - description: why it's special/recommended (1-2 sentences) or null
   - rating: if mentioned, or null
   - price: admission cost if mentioned (e.g., "Free", "$15", "$10-20") or null
   - website: URL or null
   - source: which source this came from (reddit, atlas_obscura, timeout, conde_nast, travel_leisure, web)
   - local_tip: any insider tips mentioned or null

3. PRIORITIZE places described as:
   - "hidden gem", "underrated", "locals only", "off the beaten path"
   - "best kept secret", "must visit", "don't miss"
   - Specific neighborhoods or areas to explore

4. SKIP places that are:
   - Generic chain stores/restaurants
   - Obvious tourist traps mentioned negatively
   - Places without enough detail to be useful

5. Focus on {city} locations only

OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "locations": [
    {{"name": "...", "address": null, "neighborhood": null, "category": "Hidden Gems", "description": "...", "rating": null, "price": null, "website": null, "source": "reddit", "local_tip": null}}
  ]
}}"""),
        ("human", """Parse these web pages and extract all interesting locations in {city}:

{web_pages}

Return locations as JSON. Focus on hidden gems and local favorites.""")
    ])

    chain = prompt | llm

    try:
        # Truncate pages if too long
        truncated_pages = []
        for page in web_pages:
            if len(page) > 10000:
                truncated_pages.append(page[:10000] + "\n\n[...truncated...]")
            else:
                truncated_pages.append(page)

        print(f"   -> Parsing {len(truncated_pages)} web pages with Claude Haiku...")

        response = chain.invoke({
            "web_pages": "\n\n---PAGE BREAK---\n\n".join(truncated_pages),
            "city": city
        })

        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Find JSON block
        json_start = content.find("{")
        if json_start > 0:
            content = content[json_start:]
        json_end = content.rfind("}")
        if json_end > 0:
            content = content[:json_end + 1]

        data = json.loads(content)
        locations = data.get("locations", [])

        return locations

    except Exception as e:
        print(f"   Warning: Error parsing web pages: {e}")
        return []


def _deduplicate(locations: List[Dict]) -> List[Dict]:
    """Remove duplicate locations based on name similarity."""
    seen = {}
    unique = []

    for loc in locations:
        name = (loc.get("name") or "").lower().strip()
        address = (loc.get("address") or "").lower().strip()

        # Create key from normalized name
        key = _normalize_key(name, address)

        if key and key not in seen:
            seen[key] = loc
            unique.append(loc)
        elif key in seen:
            # Merge data if we have more info
            _merge_location_data(seen[key], loc)

    return unique


def _normalize_key(name: str, address: str) -> str:
    """Create a normalized key for deduplication."""
    # Remove special characters
    name = re.sub(r"[^\w\s]", "", name)

    # Remove common words
    common_words = ["the", "a", "an", "of", "in", "at", "and"]
    words = name.split()
    filtered_words = [w for w in words if w.lower() not in common_words]
    name = " ".join(filtered_words)

    # Remove extra whitespace
    name = " ".join(name.split())

    # For address, just use first part if available
    addr_part = ""
    if address:
        addr_part = address.split(",")[0].strip()[:20]

    return f"{name}_{addr_part}".lower()


def _merge_location_data(existing: Dict, new: Dict):
    """Merge data from new record into existing, filling in nulls."""
    for key, value in new.items():
        if value is not None and existing.get(key) is None:
            existing[key] = value

    # Prefer richer descriptions
    if new.get("description") and len(new.get("description", "")) > len(existing.get("description", "")):
        existing["description"] = new["description"]

    # Keep local tips
    if new.get("local_tip") and not existing.get("local_tip"):
        existing["local_tip"] = new["local_tip"]
