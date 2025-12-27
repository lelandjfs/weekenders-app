"""
Test script for LangChain Dining Agent
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import with absolute imports
from config import setup_langsmith
from tools.neighborhood_discovery import discover_neighborhoods
from tools.google_places import search_google_places
from tools.web_search import search_web_restaurants
from tools.aggregation import aggregate_restaurants

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from langsmith import traceable


@dataclass
class DiningResult:
    """Structured result from dining agent."""
    city: str
    cuisine_filter: Optional[str]
    neighborhoods: List[str]
    total_restaurants: int
    restaurants: List[Dict[str, Any]]
    sources: Dict[str, int]
    execution_time_seconds: float
    timestamp: str


class DiningAgent:
    """LangChain-compatible restaurant discovery agent."""

    def __init__(
        self,
        project_name: str = "weekenders-dining-agent",
        enable_tracing: bool = True,
        output_dir: str = None
    ):
        self.project_name = project_name
        self.enable_tracing = enable_tracing
        self.output_dir = output_dir or str(Path(__file__).parent / "tests")
        setup_langsmith(project_name, enable_tracing)

    @traceable(name="dining_agent_run")
    def run(
        self,
        city: str,
        cuisine_type: str = None,
        save_results: bool = True
    ) -> DiningResult:
        """Run the dining agent for a city."""
        start_time = datetime.now()
        timestamp = start_time.isoformat()

        print(f"\n{'='*60}")
        print(f"🍽️  DINING AGENT - {city.upper()}")
        print(f"{'='*60}")

        # Step 1: Discover neighborhoods
        print(f"\n📍 Step 1: Discovering neighborhoods...")
        neighborhoods = discover_neighborhoods.invoke({
            "city": city,
            "max_neighborhoods": 5
        })

        # Step 2: Search Google Places
        print(f"\n🔍 Step 2: Searching Google Places...")
        google_results = search_google_places.invoke({
            "city": city,
            "neighborhoods": neighborhoods,
            "cuisine_type": cuisine_type
        })

        # Step 3: Search web sources
        print(f"\n🌐 Step 3: Searching web sources...")
        web_pages = search_web_restaurants.invoke({
            "city": city,
            "neighborhoods": neighborhoods
        })

        # Step 4: Aggregate and deduplicate
        print(f"\n🤖 Step 4: Aggregating results...")
        restaurants = aggregate_restaurants.invoke({
            "google_places_results": google_results,
            "web_page_contents": web_pages,
            "city": city,
            "neighborhoods": neighborhoods
        })

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Count sources
        source_counts = {}
        for r in restaurants:
            source = r.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        # Build result
        result = DiningResult(
            city=city,
            cuisine_filter=cuisine_type,
            neighborhoods=neighborhoods,
            total_restaurants=len(restaurants),
            restaurants=restaurants,
            sources=source_counts,
            execution_time_seconds=execution_time,
            timestamp=timestamp
        )

        # Save results if requested
        if save_results:
            self._save_results(result)

        # Print summary
        self._print_summary(result)

        return result

    def _save_results(self, result: DiningResult):
        """Save results to a timestamped file."""
        city_folder = result.city.replace(" ", "_")
        output_path = Path(self.output_dir) / city_folder
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)

        print(f"\n📁 Results saved to: {filepath}")

    def _print_summary(self, result: DiningResult):
        """Print a summary of results."""
        print(f"\n{'='*60}")
        print(f"✅ DINING AGENT COMPLETE")
        print(f"{'='*60}")
        print(f"   City: {result.city}")
        print(f"   Neighborhoods: {', '.join(result.neighborhoods) if result.neighborhoods else 'City-wide'}")
        print(f"   Total Restaurants: {result.total_restaurants}")
        print(f"   Sources: {result.sources}")
        print(f"   Execution Time: {result.execution_time_seconds:.2f}s")
        print(f"{'='*60}")

        if result.restaurants:
            print(f"\n🍽️  TOP 10 RESTAURANTS:")
            for i, r in enumerate(result.restaurants[:10], 1):
                name = r.get("name", "Unknown")
                rating = r.get("rating")
                source = r.get("source", "")
                neighborhood = r.get("neighborhood", "")

                rating_str = f"⭐ {rating}" if rating else ""
                hood_str = f"• {neighborhood}" if neighborhood else ""

                print(f"   {i}. {name} {rating_str} {hood_str}")
                print(f"      Source: {source}")

        print(f"\n{'='*60}\n")


def run_dining_agent(city: str, cuisine_type: str = None) -> DiningResult:
    """Convenience function to run the dining agent."""
    agent = DiningAgent()
    return agent.run(city, cuisine_type=cuisine_type)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the LangChain Dining Agent")
    parser.add_argument("city", help="City to search (e.g., 'Austin', 'New York')")
    parser.add_argument("--cuisine", "-c", type=str, default=None,
                       help="Cuisine type filter")

    args = parser.parse_args()

    print(f"\n🍽️  Testing LangChain Dining Agent for: {args.city}")
    if args.cuisine:
        print(f"   Cuisine filter: {args.cuisine}")

    result = run_dining_agent(args.city, cuisine_type=args.cuisine)
    print(f"\nTotal: {result.total_restaurants} restaurants")
