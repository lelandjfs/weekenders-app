"""
Aggregation Tool for LangChain
===============================

LangChain-compatible tool for aggregating and deduplicating restaurant results.
Uses Claude Haiku to parse web pages and combine with Google Places data.
"""

import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY


class AggregationInput(BaseModel):
    """Input schema for restaurant aggregation."""
    google_places_results: List[Dict[str, Any]] = Field(
        description="Structured results from Google Places"
    )
    web_page_contents: List[str] = Field(
        description="Raw page contents from web search"
    )
    city: str = Field(description="City name for context")
    neighborhoods: List[str] = Field(
        default=[],
        description="List of neighborhoods for context"
    )


@tool(args_schema=AggregationInput)
def aggregate_restaurants(
    google_places_results: List[Dict[str, Any]],
    web_page_contents: List[str],
    city: str,
    neighborhoods: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Aggregate restaurant results from multiple sources.

    Uses Claude Haiku to parse web pages, then combines with
    Google Places results and deduplicates.

    Args:
        google_places_results: Structured results from Google Places
        web_page_contents: Raw page contents from web search
        city: City name for context
        neighborhoods: List of neighborhoods for context

    Returns:
        Deduplicated, ranked list of restaurants
    """
    all_restaurants = []

    # Add Google Places results directly (already structured)
    for r in google_places_results:
        r["source"] = "google_places"
        all_restaurants.append(r)

    print(f"   → Starting with {len(google_places_results)} Google Places results")

    # Parse web pages with Claude Haiku
    if web_page_contents:
        web_restaurants = _parse_web_pages(web_page_contents, city)
        all_restaurants.extend(web_restaurants)
        print(f"   → Added {len(web_restaurants)} restaurants from web sources")

    # Deduplicate
    unique_restaurants = _deduplicate(all_restaurants)
    print(f"   → After deduplication: {len(unique_restaurants)} unique restaurants")

    # Sort by rating (descending), then by review count
    unique_restaurants.sort(
        key=lambda x: (
            -(x.get("rating") or 0),
            -(x.get("review_count") or 0)
        )
    )

    return unique_restaurants


def _parse_web_pages(
    web_pages: List[str],
    city: str
) -> List[Dict[str, Any]]:
    """Use Claude Haiku to parse restaurant details from web pages."""
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=8000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an extraction engine. Extract restaurant information from the web page content provided.

Rules:
1. Extract EVERY restaurant mentioned in the web pages
2. For each restaurant, extract:
   - name: restaurant name (REQUIRED)
   - address: full address or null
   - neighborhood: neighborhood name or null
   - rating: numeric rating (1-5 or 1-10 scale) or null
   - review_count: number of reviews or null
   - price_level: "$", "$$", "$$$", or "$$$$" or null
   - cuisine_type: type of cuisine or null
   - website: restaurant website or null
   - description: brief description (1-2 sentences) or null
   - source: which source mentioned this (eater, infatuation, reddit, or web)

3. If a field is missing, set it to null - DO NOT guess
4. Focus on restaurants in {city}
5. Skip restaurants that are clearly not in {city}

OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "restaurants": [
    {{"name": "...", "address": null, "neighborhood": null, "rating": null, "review_count": null, "price_level": null, "cuisine_type": null, "website": null, "description": null, "source": "eater"}}
  ]
}}"""),
        ("human", """Parse these web pages and extract all restaurants in {city}:

{web_pages}

Return restaurants as JSON.""")
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

        print(f"   → Parsing {len(truncated_pages)} web pages with Claude Haiku...")

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
        restaurants = data.get("restaurants", [])

        return restaurants

    except Exception as e:
        print(f"   ⚠️ Error parsing web pages: {e}")
        return []


def _deduplicate(restaurants: List[Dict]) -> List[Dict]:
    """Remove duplicate restaurants based on name similarity."""
    seen = {}  # name_key -> restaurant
    unique = []

    for r in restaurants:
        name = (r.get("name") or "").lower().strip()

        # Normalize name for comparison
        name_key = _normalize_name(name)

        if name_key and name_key not in seen:
            seen[name_key] = r
            unique.append(r)
        elif name_key in seen:
            # Merge data if we have more info in the new record
            existing = seen[name_key]
            _merge_restaurant_data(existing, r)

    return unique


def _normalize_name(name: str) -> str:
    """Normalize restaurant name for deduplication."""
    # Remove common suffixes
    name = re.sub(r"\s*(restaurant|cafe|bar|grill|kitchen|eatery|bistro)$", "", name, flags=re.IGNORECASE)

    # Remove special characters
    name = re.sub(r"[^\w\s]", "", name)

    # Remove extra whitespace
    name = " ".join(name.split())

    return name.lower()


def _merge_restaurant_data(existing: Dict, new: Dict):
    """Merge data from new record into existing, filling in nulls."""
    for key, value in new.items():
        if value is not None and existing.get(key) is None:
            existing[key] = value

    # If new has a description and existing doesn't, use new
    if new.get("description") and not existing.get("description"):
        existing["description"] = new["description"]
