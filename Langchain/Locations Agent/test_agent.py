"""
Test script for LangChain Locations Agent
==========================================

Discovers attractions, hidden gems, and local favorites for a given city.
Not date-specific - focuses on museums, parks, landmarks, unique spots.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langsmith import traceable

from config import setup_langsmith
from tools.google_places import search_google_places_attractions
from tools.web_search import search_web_locations
from tools.aggregation import aggregate_locations


@dataclass
class LocationsResult:
    """Structured result from locations agent."""
    city: str
    total_locations: int
    locations: List[Dict[str, Any]]
    sources: Dict[str, int]
    categories: Dict[str, int]
    execution_time_seconds: float
    timestamp: str


class LocationsAgent:
    """LangChain-compatible locations discovery agent."""

    def __init__(
        self,
        project_name: str = "weekenders-locations-agent",
        enable_tracing: bool = True,
        output_dir: str = None
    ):
        self.project_name = project_name
        self.enable_tracing = enable_tracing
        self.output_dir = output_dir or str(Path(__file__).parent / "tests")
        setup_langsmith(project_name, enable_tracing)

    @traceable(name="locations_agent_run")
    def run(
        self,
        city: str,
        save_results: bool = True
    ) -> LocationsResult:
        """
        Run the locations agent for a city.

        Args:
            city: City name (e.g., "San Francisco", "Austin")
            save_results: Whether to save results to disk

        Returns:
            LocationsResult with all discovered locations
        """
        start_time = datetime.now()
        timestamp = start_time.isoformat()

        print(f"\n{'='*60}")
        print(f"LOCATIONS AGENT - {city.upper()}")
        print(f"{'='*60}")
        print(f"Discovering attractions, hidden gems, and local favorites...")

        # Step 1: Search Google Places for attractions
        print(f"\nStep 1: Searching Google Places...")
        google_results = search_google_places_attractions.invoke({
            "city": city,
            "attraction_types": []
        })

        # Step 2: Search web sources for hidden gems
        print(f"\nStep 2: Searching web sources (Reddit, Atlas Obscura, Timeout)...")
        web_pages = search_web_locations.invoke({
            "city": city
        })

        # Step 3: Aggregate and deduplicate
        print(f"\nStep 3: Aggregating results...")
        locations = aggregate_locations.invoke({
            "google_places_results": google_results,
            "web_page_contents": web_pages,
            "city": city
        })

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Count sources and categories
        source_counts = {}
        category_counts = {}
        for loc in locations:
            source = loc.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

            category = loc.get("category", "Other")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Build result
        result = LocationsResult(
            city=city,
            total_locations=len(locations),
            locations=locations,
            sources=source_counts,
            categories=category_counts,
            execution_time_seconds=execution_time,
            timestamp=timestamp
        )

        # Save results if requested
        if save_results:
            self._save_results(result)

        # Print summary
        self._print_summary(result)

        return result

    def _save_results(self, result: LocationsResult):
        """Save results to a timestamped file."""
        city_folder = result.city.replace(" ", "_")
        output_path = Path(self.output_dir) / city_folder
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)

        print(f"\nResults saved to: {filepath}")

    def _print_summary(self, result: LocationsResult):
        """Print a summary of results."""
        print(f"\n{'='*60}")
        print(f"LOCATIONS AGENT COMPLETE")
        print(f"{'='*60}")
        print(f"   City: {result.city}")
        print(f"   Total Locations: {result.total_locations}")
        print(f"   Sources: {result.sources}")
        print(f"   Categories: {result.categories}")
        print(f"   Execution Time: {result.execution_time_seconds:.2f}s")
        print(f"{'='*60}")

        if result.locations:
            print(f"\nTOP 15 LOCATIONS:")
            for i, loc in enumerate(result.locations[:15], 1):
                name = loc.get("name", "Unknown")
                category = loc.get("category", "")
                source = loc.get("source", "")
                rating = loc.get("rating")
                description = loc.get("description", "")

                print(f"\n   {i}. {name}")
                if category:
                    print(f"      Category: {category}")
                if rating:
                    print(f"      Rating: {rating}")
                if description:
                    # Truncate long descriptions
                    desc = description[:100] + "..." if len(description) > 100 else description
                    print(f"      {desc}")
                print(f"      Source: {source}")

                # Show local tip if available
                local_tip = loc.get("local_tip")
                if local_tip:
                    tip = local_tip[:80] + "..." if len(local_tip) > 80 else local_tip
                    print(f"      Tip: {tip}")

        print(f"\n{'='*60}\n")


def run_locations_agent(city: str) -> LocationsResult:
    """Convenience function to run the locations agent."""
    agent = LocationsAgent()
    return agent.run(city)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the LangChain Locations Agent")
    parser.add_argument("city", help="City to search (e.g., 'Austin', 'Portland')")

    args = parser.parse_args()

    print(f"\nTesting LangChain Locations Agent for: {args.city}")

    result = run_locations_agent(args.city)
    print(f"\nTotal: {result.total_locations} locations")
