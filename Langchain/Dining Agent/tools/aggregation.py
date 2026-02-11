"""
Aggregation Tool for LangChain
===============================

LangChain-compatible tool for aggregating and deduplicating restaurant results.
Uses Claude Haiku to parse web pages and combine with Google Places data.

Optimized with:
- Pre-filtering to extract only restaurant-relevant content
- Batch processing for parallel LLM calls
"""

import json
import re
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY

# Import content filter
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weekender"))
from content_filter import filter_content, batch_pages


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
@traceable(name="aggregate_restaurants_llm", run_type="chain")
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

    print(f"   -> Starting with {len(google_places_results)} Google Places results")

    # Parse web pages with Claude Haiku (with filtering and batching)
    if web_page_contents:
        web_restaurants = _parse_web_pages_batched(web_page_contents, city)
        all_restaurants.extend(web_restaurants)
        print(f"   -> Added {len(web_restaurants)} restaurants from web sources")

    # Deduplicate
    unique_restaurants = _deduplicate(all_restaurants)
    print(f"   -> After deduplication: {len(unique_restaurants)} unique restaurants")

    # Sort by rating (descending), then by review count
    unique_restaurants.sort(
        key=lambda x: (
            -(x.get("rating") or 0),
            -(x.get("review_count") or 0)
        )
    )

    return unique_restaurants


def _parse_web_pages_batched(
    web_pages: List[str],
    city: str,
    batch_size: int = 3,
    max_workers: int = 3
) -> List[Dict[str, Any]]:
    """Parse web pages in batches with parallel processing."""

    # Step 1: Pre-filter content to reduce context
    print(f"   -> Pre-filtering {len(web_pages)} pages...")
    filtered_pages = []
    for page in web_pages:
        filtered = filter_content(page, 'restaurants', max_lines=100)
        if filtered.strip():  # Only keep pages with relevant content
            filtered_pages.append(filtered)

    print(f"   -> After filtering: {len(filtered_pages)} pages with relevant content")

    if not filtered_pages:
        return []

    # Step 2: Batch pages
    batches = batch_pages(filtered_pages, batch_size)
    print(f"   -> Processing {len(batches)} batches in parallel...")

    # Step 3: Process batches in parallel
    all_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_parse_batch, batch, city): i
            for i, batch in enumerate(batches)
        }

        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                print(f"   Warning: Batch {batch_idx} failed: {e}")

    return all_results


def _parse_batch(pages: List[str], city: str) -> List[Dict[str, Any]]:
    """Parse a batch of pages with Claude Haiku."""
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=4000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an extraction engine. Extract restaurant information from the web content provided.

Rules:
1. Extract EVERY restaurant mentioned
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
        ("human", """Parse this content and extract all restaurants in {city}:

{web_pages}

Return restaurants as JSON.""")
    ])

    chain = prompt | llm

    try:
        response = chain.invoke({
            "web_pages": "\n\n---\n\n".join(pages),
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
        return data.get("restaurants", [])

    except Exception as e:
        print(f"   Warning: Parse error: {e}")
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
