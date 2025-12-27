"""
Dining Agent
=============

Discovers restaurant recommendations for a city by combining:
1. Neighborhood discovery (find trendy food areas)
2. Google Places search (structured data)
3. Web search (Eater, Reddit, Infatuation)
4. Aggregation with Claude Haiku (parse and deduplicate)
"""

import json
from datetime import datetime
from typing import Dict, Any, List

from tools.neighborhood_discovery import discover_neighborhoods
from tools.google_places import search_google_places
from tools.web_search import search_web_restaurants
from tools.aggregation import aggregate_restaurants


class DiningAgent:
    """
    Agent for discovering restaurant recommendations in a city.

    Uses multiple data sources and AI-powered aggregation
    to provide comprehensive, deduplicated restaurant lists.
    """

    def __init__(self):
        """Initialize the Dining Agent."""
        pass

    def run(self, city: str, cuisine_type: str = None) -> Dict[str, Any]:
        """
        Run the dining agent for a city.

        Args:
            city: City name (e.g., "San Francisco", "Austin")
            cuisine_type: Optional cuisine filter (e.g., "Italian", "Mexican")

        Returns:
            Dictionary with:
                - city: City searched
                - neighborhoods: Discovered neighborhoods
                - restaurants: List of restaurant objects
                - sources: Count by source
                - timestamp: When the search was run
        """
        print(f"\n{'='*60}")
        print(f"🍽️  DINING AGENT - {city.upper()}")
        print(f"{'='*60}")

        timestamp = datetime.now().isoformat()

        # Step 1: Discover neighborhoods
        print(f"\n📍 Step 1: Discovering neighborhoods...")
        neighborhoods = discover_neighborhoods(city)

        # Step 2: Search Google Places
        print(f"\n🔍 Step 2: Searching Google Places...")
        google_results = search_google_places(
            city=city,
            neighborhoods=neighborhoods,
            cuisine_type=cuisine_type
        )

        # Step 3: Search web sources
        print(f"\n🌐 Step 3: Searching web sources...")
        web_pages = search_web_restaurants(
            city=city,
            neighborhoods=neighborhoods
        )

        # Step 4: Aggregate and deduplicate
        print(f"\n🤖 Step 4: Aggregating results with Claude Haiku...")
        restaurants = aggregate_restaurants(
            google_places_results=google_results,
            web_page_contents=web_pages,
            city=city,
            neighborhoods=neighborhoods
        )

        # Count sources
        source_counts = {}
        for r in restaurants:
            source = r.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        # Build result
        result = {
            "city": city,
            "cuisine_filter": cuisine_type,
            "neighborhoods": neighborhoods,
            "restaurants": restaurants,
            "total_restaurants": len(restaurants),
            "sources": source_counts,
            "timestamp": timestamp
        }

        # Print summary
        print(f"\n{'='*60}")
        print(f"✅ DINING AGENT COMPLETE")
        print(f"{'='*60}")
        print(f"   City: {city}")
        print(f"   Neighborhoods: {', '.join(neighborhoods) if neighborhoods else 'City-wide'}")
        print(f"   Total Restaurants: {len(restaurants)}")
        print(f"   Sources: {source_counts}")
        print(f"{'='*60}\n")

        return result

    def format_results(self, result: Dict[str, Any]) -> str:
        """
        Format results for display.

        Args:
            result: Result dictionary from run()

        Returns:
            Formatted string for printing
        """
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"🍽️  RESTAURANTS IN {result['city'].upper()}")
        lines.append(f"{'='*60}")

        # Show neighborhoods
        neighborhoods = result.get("neighborhoods", [])
        if neighborhoods:
            lines.append(f"\n📍 NEIGHBORHOODS IDENTIFIED:")
            for hood in neighborhoods:
                lines.append(f"   • {hood}")
            lines.append("")

        restaurants = result.get("restaurants", [])

        for i, r in enumerate(restaurants, 1):
            name = r.get("name", "Unknown")
            rating = r.get("rating")
            reviews = r.get("review_count")
            price = r.get("price_level", "")
            cuisine = r.get("cuisine_type", "")
            neighborhood = r.get("neighborhood", "")
            source = r.get("source", "")

            # Build rating string
            rating_str = f"⭐ {rating}" if rating else ""
            reviews_str = f"({reviews} reviews)" if reviews else ""

            lines.append(f"{i}. {name}")
            if rating_str or reviews_str:
                lines.append(f"   {rating_str} {reviews_str}".strip())

            details = []
            if price:
                details.append(price)
            if cuisine:
                details.append(cuisine)
            if neighborhood:
                details.append(neighborhood)
            if details:
                lines.append(f"   {' • '.join(details)}")

            if r.get("description"):
                lines.append(f"   📝 {r['description'][:100]}...")

            lines.append(f"   📍 Source: {source}")
            lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point for testing."""
    agent = DiningAgent()

    # Test with San Francisco
    result = agent.run("San Francisco")

    # Print formatted results
    print(agent.format_results(result))

    # Print top 10
    print("\n📋 TOP 10 RESTAURANTS:")
    for i, r in enumerate(result["restaurants"][:10], 1):
        print(f"   {i}. {r['name']} - ⭐ {r.get('rating', 'N/A')}")


if __name__ == "__main__":
    main()
