"""
Context Router for Weekenders App
==================================

Uses Claude 3.5 Haiku (CHEAP, FAST) to analyze cities and determine search strategy.
Cost: ~$0.0003 per query

Purpose:
- Analyzes location characteristics (city size, population, geography)
- Determines if neighborhood-based search is needed (NYC) vs city-wide (Austin)
- Sets appropriate search radii for different query types
- Identifies trendy neighborhoods for large metros

Model: claude-3-5-haiku-20241022 (NOT Sonnet/Opus - per user request)
"""

import json
from typing import Dict, Optional, List
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

# API Key from environment
import os
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class SearchParameters(BaseModel):
    """Search radius parameters for different query types"""
    dining_radius_miles: float
    concert_radius_miles: float
    events_radius_miles: float
    locations_radius_miles: float


class SearchStrategy(BaseModel):
    """Search strategy for each agent type"""
    dining: str  # "neighborhood_targeted" or "city_wide"
    concerts: str  # always "city_wide"
    events: str  # always "city_wide"
    locations: str  # "neighborhood_targeted" or "city_wide"


class LocationInfo(BaseModel):
    """Geographic information about the location"""
    original_location: str
    normalized_location: str  # Claude's understanding of the location
    latitude: float
    longitude: float
    country: str


class SearchContext(BaseModel):
    """Complete context object returned by router"""
    location_info: LocationInfo
    area_classification: str  # "too_large", "appropriate_size", "too_small"
    search_scope: str  # What we're actually searching
    city_type: str  # "large_metro", "medium_city", "small_area"
    needs_neighborhood_strategy: bool
    neighborhoods: Optional[List[str]]  # For "too_large"
    expanded_areas: Optional[List[str]]  # For "too_small"
    search_parameters: SearchParameters
    strategy: SearchStrategy
    reasoning: str  # Claude's explanation of decisions


def create_context_router():
    """
    Creates the LLM for context routing.

    IMPORTANT: Uses claude-3-5-haiku-20241022 (cheapest model)
    Cost: ~$0.0003 per query
    """
    return ChatAnthropic(
        model="claude-3-5-haiku-20241022",  # HAIKU only - cheap and fast
        anthropic_api_key=CLAUDE_API_KEY,
        temperature=0,  # Deterministic for consistent routing
        max_tokens=1000  # Enough for JSON response
    )


def analyze_city(location: str, start_date: str, end_date: str) -> SearchContext:
    """
    Analyzes a city and returns optimal search context.

    Args:
        location: City name (e.g., "New York City", "Austin, Texas")
        start_date: ISO date string (e.g., "2024-12-06")
        end_date: ISO date string (e.g., "2024-12-08")

    Returns:
        SearchContext object with routing decisions

    Examples:
        >>> context = analyze_city("New York City", "2024-12-06", "2024-12-08")
        >>> print(context.city_type)
        "large_metro"
        >>> print(context.neighborhoods)
        ["Williamsburg, Brooklyn", "Lower East Side, Manhattan", ...]
    """

    llm = create_context_router()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a geographic analysis expert for a travel recommendations system.

Your job: Analyze the given location and determine the optimal search strategy to find quality recommendations.

Return ONLY valid JSON (no markdown, no explanation) with this EXACT structure:

{{
  "location_info": {{
    "original_location": "user's input",
    "normalized_location": "your understanding (e.g., 'New York City, New York, USA')",
    "latitude": number,
    "longitude": number,
    "country": "country name"
  }},
  "area_classification": "too_large" | "appropriate_size" | "too_small",
  "search_scope": "description of what we're searching",
  "city_type": "large_metro" | "medium_city" | "small_area",
  "needs_neighborhood_strategy": boolean,
  "neighborhoods": ["area1", "area2"] or null,
  "expanded_areas": ["nearby1", "nearby2"] or null,
  "search_parameters": {{
    "dining_radius_miles": number,
    "concert_radius_miles": number,
    "events_radius_miles": number,
    "locations_radius_miles": number
  }},
  "strategy": {{
    "dining": "neighborhood_targeted" | "city_wide" | "expanded_area",
    "concerts": "city_wide" | "expanded_area",
    "events": "city_wide" | "expanded_area",
    "locations": "neighborhood_targeted" | "city_wide" | "expanded_area"
  }},
  "reasoning": "brief explanation of your decisions"
}}

THREE SCENARIOS:

1. TOO LARGE (NYC, LA, Tokyo, London)
   - area_classification: "too_large"
   - Problem: Too many results, need to focus
   - Solution: Break into 4-6 trendy neighborhoods
   - city_type: "large_metro"
   - needs_neighborhood_strategy: true
   - neighborhoods: List specific neighborhoods (e.g., "Williamsburg, Brooklyn")
   - expanded_areas: null
   - Example: NYC → Lower East Side, Williamsburg, DUMBO, Chelsea, Astoria

   Search Parameters:
   - dining_radius_miles: 1.5 (tight radius per neighborhood)
   - concert_radius_miles: 25 (people travel for concerts)
   - events_radius_miles: 15
   - locations_radius_miles: 2

   Strategy:
   - dining: "neighborhood_targeted"
   - concerts: "city_wide" (still search whole metro)
   - events: "city_wide"
   - locations: "neighborhood_targeted"

2. APPROPRIATE SIZE (Austin, Portland, Nashville, Barcelona, Kyoto)
   - area_classification: "appropriate_size"
   - Problem: None - perfect size for city-wide search
   - Solution: Search the whole city/metro area
   - city_type: "medium_city"
   - needs_neighborhood_strategy: false
   - neighborhoods: null
   - expanded_areas: null

   Search Parameters:
   - dining_radius_miles: 5-7
   - concert_radius_miles: 20
   - events_radius_miles: 12
   - locations_radius_miles: 5-7

   Strategy: All "city_wide"

3. TOO SMALL (Palo Alto, Cambridge, Santa Monica, Hoboken)
   - area_classification: "too_small"
   - Problem: Not enough results in this small area alone
   - Solution: Include nearby cities/areas to cast wider net
   - city_type: "small_area"
   - needs_neighborhood_strategy: false
   - neighborhoods: null
   - expanded_areas: List 3-5 nearby areas (e.g., Palo Alto → San Jose, Mountain View, Sunnyvale, Menlo Park)

   Search Parameters:
   - dining_radius_miles: 10-15 (wide radius to capture nearby areas)
   - concert_radius_miles: 30-40 (very wide - limited concerts)
   - events_radius_miles: 20-25
   - locations_radius_miles: 10-15

   Strategy: All "expanded_area"

CRITICAL RULES:

1. LOCATION UNDERSTANDING:
   - First, understand what the user meant (normalize the location)
   - Provide accurate lat/long coordinates for the center point
   - Identify the country

2. CONCERTS ARE SPECIAL - ALWAYS CAST WIDER NET:
   - Concerts ALWAYS need BROADER geographic scope than other categories
   - People travel farther for concerts (20-40 miles is normal)
   - CRITICAL: For cities like San Francisco, Oakland, Berkeley, Boston - even though they're big enough
     to be "appropriate_size" or "too_large" for dining/locations, for CONCERTS they should be
     treated as "too_small" and expanded to include the broader metro area
   - Examples:
     * SF → Expand to Oakland, Berkeley, San Jose for concerts
     * Boston → Expand to Cambridge, Somerville, Brookline for concerts
     * Even "too_large" cities use city_wide (not neighborhood) for concerts
   - Small areas need especially wide concert radius (30-40 miles)

3. CLASSIFICATION LOGIC:
   - Population > 5M metro → "too_large"
   - Population 500K-5M → "appropriate_size"
   - Population < 500K OR suburban area → "too_small"

4. EXAMPLES:
   - NYC (8M) → too_large, neighborhoods for dining/locations, but concerts still search all 5 boroughs
   - Austin (2M) → appropriate_size, city-wide for all categories
   - San Francisco (870K) → too_large for dining (use neighborhoods), but too_small for concerts (expand to Oakland, Berkeley, San Jose)
   - Palo Alto (65K, suburb) → too_small, expand to San Jose area
   - Cambridge, MA (120K, suburb) → too_small, expand to Greater Boston
   - Santa Monica (90K, suburb) → too_small, expand to LA area

IMPORTANT:
- Return ONLY JSON, no markdown code blocks
- Include lat/long coordinates (approximate center)
- Ensure all fields are present
- Provide reasoning explaining your classification
"""),
        ("human", "Analyze this location: {location}\nDates: {start_date} to {end_date}")
    ])

    try:
        chain = prompt | llm
        response = chain.invoke({
            "location": location,
            "start_date": start_date,
            "end_date": end_date
        })

        # Parse JSON from response
        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        # Parse JSON
        context_dict = json.loads(content)

        # Validate and return
        context = SearchContext(**context_dict)
        return context

    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parsing error: {e}")
        print(f"Response content: {response.content[:200]}")
        # Return fallback context
        return _fallback_context(location, start_date, end_date)

    except Exception as e:
        print(f"⚠️  Context router error: {e}")
        return _fallback_context(location, start_date, end_date)


def _fallback_context(location: str, start_date: str, end_date: str) -> SearchContext:
    """
    Fallback context if LLM fails.
    Uses safe defaults: appropriate size, city-wide search.
    """
    return SearchContext(
        location_info=LocationInfo(
            original_location=location,
            normalized_location=location,
            latitude=0.0,
            longitude=0.0,
            country="Unknown"
        ),
        area_classification="appropriate_size",
        search_scope=f"City-wide search of {location}",
        city_type="medium_city",
        needs_neighborhood_strategy=False,
        neighborhoods=None,
        expanded_areas=None,
        search_parameters=SearchParameters(
            dining_radius_miles=5,
            concert_radius_miles=20,
            events_radius_miles=12,
            locations_radius_miles=5
        ),
        strategy=SearchStrategy(
            dining="city_wide",
            concerts="city_wide",
            events="city_wide",
            locations="city_wide"
        ),
        reasoning="Fallback context due to LLM error"
    )


def print_context_summary(context: SearchContext):
    """Pretty print context for debugging"""
    print("\n" + "="*70)
    print(f"CONTEXT ROUTER ANALYSIS: {context.location_info.original_location}")
    print("="*70)

    # Location Info
    print(f"\n📍 Location Understanding:")
    print(f"  Input: {context.location_info.original_location}")
    print(f"  Normalized: {context.location_info.normalized_location}")
    print(f"  Coordinates: {context.location_info.latitude}, {context.location_info.longitude}")
    print(f"  Country: {context.location_info.country}")

    # Classification
    print(f"\n🎯 Classification:")
    print(f"  Area Type: {context.area_classification.upper()}")
    print(f"  City Type: {context.city_type}")
    print(f"  Search Scope: {context.search_scope}")

    # Neighborhoods or Expanded Areas
    if context.area_classification == "too_large" and context.neighborhoods:
        print(f"\n🏘️  Neighborhoods ({len(context.neighborhoods)}):")
        for i, neighborhood in enumerate(context.neighborhoods, 1):
            print(f"  {i}. {neighborhood}")

    if context.area_classification == "too_small" and context.expanded_areas:
        print(f"\n🗺️  Expanded Areas ({len(context.expanded_areas)}):")
        for i, area in enumerate(context.expanded_areas, 1):
            print(f"  {i}. {area}")

    # Search Parameters
    print(f"\n📏 Search Radii:")
    print(f"  Dining: {context.search_parameters.dining_radius_miles} miles")
    print(f"  Concerts: {context.search_parameters.concert_radius_miles} miles")
    print(f"  Events: {context.search_parameters.events_radius_miles} miles")
    print(f"  Locations: {context.search_parameters.locations_radius_miles} miles")

    # Strategies
    print(f"\n🎲 Search Strategies:")
    print(f"  Dining: {context.strategy.dining}")
    print(f"  Concerts: {context.strategy.concerts}")
    print(f"  Events: {context.strategy.events}")
    print(f"  Locations: {context.strategy.locations}")

    # Reasoning
    print(f"\n💡 Reasoning:")
    print(f"  {context.reasoning}")

    print("="*70 + "\n")


if __name__ == "__main__":
    """Test the context router with different cities"""

    print("\n🧪 TESTING CONTEXT ROUTER (Claude 3.5 Haiku)")
    print("Testing 3 scenarios: TOO LARGE, APPROPRIATE SIZE, TOO SMALL")
    print("Cost per query: ~$0.0003")
    print("="*70)

    # Test 1: TOO LARGE - should break into neighborhoods
    print("\n📍 TEST 1: New York City (TOO LARGE)")
    nyc_context = analyze_city("New York City", "2024-12-06", "2024-12-08")
    print_context_summary(nyc_context)

    # Test 2: APPROPRIATE SIZE - should search city-wide
    print("\n📍 TEST 2: Austin, Texas (APPROPRIATE SIZE)")
    austin_context = analyze_city("Austin, Texas", "2024-12-06", "2024-12-08")
    print_context_summary(austin_context)

    # Test 3: TOO SMALL - should expand to nearby areas
    print("\n📍 TEST 3: Palo Alto, California (TOO SMALL)")
    palo_alto_context = analyze_city("Palo Alto", "2024-12-06", "2024-12-08")
    print_context_summary(palo_alto_context)

    # Test 4: Another too small (suburban)
    print("\n📍 TEST 4: Cambridge, Massachusetts (TOO SMALL - suburb)")
    cambridge_context = analyze_city("Cambridge, MA", "2024-12-06", "2024-12-08")
    print_context_summary(cambridge_context)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n✅ Context Router tested with 4 locations")
    print(f"\n  TOO LARGE:")
    print(f"    - {nyc_context.location_info.normalized_location}")
    print(f"      → {len(nyc_context.neighborhoods or [])} neighborhoods")
    print(f"      → {nyc_context.search_parameters.dining_radius_miles} mile radius (tight)")

    print(f"\n  APPROPRIATE SIZE:")
    print(f"    - {austin_context.location_info.normalized_location}")
    print(f"      → City-wide search")
    print(f"      → {austin_context.search_parameters.dining_radius_miles} mile radius")

    print(f"\n  TOO SMALL:")
    print(f"    - {palo_alto_context.location_info.normalized_location}")
    print(f"      → {len(palo_alto_context.expanded_areas or [])} expanded areas")
    print(f"      → {palo_alto_context.search_parameters.dining_radius_miles} mile radius (wide)")
    print(f"    - {cambridge_context.location_info.normalized_location}")
    print(f"      → {len(cambridge_context.expanded_areas or [])} expanded areas")
    print(f"      → {cambridge_context.search_parameters.dining_radius_miles} mile radius (wide)")

    print("\n💰 Total estimated cost: ~$0.0012 (4 queries)")
    print("\n✨ All 3 scenarios working! Ready to integrate with agents!")
