"""
LangChain Dining Agent
=======================

Main restaurant discovery agent using LangChain patterns.
Orchestrates multiple tools for comprehensive restaurant recommendations.

Features:
- Full LangSmith tracing for observability
- Modular tool-based architecture
- Neighborhood-first discovery
- Multi-source aggregation (Google Places + Web)

Usage:
    from langchain_final import DiningAgent

    agent = DiningAgent()
    results = agent.run("San Francisco")
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from langsmith import traceable

# Local imports
from .config import setup_langsmith
from .tools import (
    discover_neighborhoods,
    search_google_places,
    search_web_restaurants,
    aggregate_restaurants
)


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
    """
    LangChain-compatible restaurant discovery agent.

    Orchestrates multiple tools to find restaurants:
    1. Discovers trendy food neighborhoods
    2. Searches Google Places per neighborhood
    3. Searches web sources (Eater, Reddit, Infatuation)
    4. Aggregates and deduplicates all results

    All operations are traced in LangSmith for observability.
    """

    def __init__(
        self,
        project_name: str = "weekenders-dining-agent",
        enable_tracing: bool = True,
        output_dir: str = None
    ):
        """
        Initialize the Dining Agent.

        Args:
            project_name: LangSmith project name for tracing
            enable_tracing: Whether to enable LangSmith tracing
            output_dir: Directory to save results (optional)
        """
        self.project_name = project_name
        self.enable_tracing = enable_tracing
        self.output_dir = output_dir or str(Path(__file__).parent / "tests")

        # Setup LangSmith tracing
        setup_langsmith(project_name, enable_tracing)

    @traceable(name="dining_agent_run")
    def run(
        self,
        city: str,
        cuisine_type: str = None,
        save_results: bool = True
    ) -> DiningResult:
        """
        Run the dining agent for a city.

        Args:
            city: City name (e.g., "San Francisco", "New York")
            cuisine_type: Optional cuisine filter (e.g., "Italian", "Mexican")
            save_results: Whether to save results to disk

        Returns:
            DiningResult with all discovered restaurants
        """
        start_time = datetime.now()
        timestamp = start_time.isoformat()

        print(f"\n{'='*60}")
        print(f"🍽️  DINING AGENT - {city.upper()}")
        print(f"{'='*60}")

        # Step 1: Discover neighborhoods
        print(f"\n📍 Step 1: Discovering neighborhoods...")
        neighborhoods = self._discover_neighborhoods(city)

        # Step 2: Search Google Places
        print(f"\n🔍 Step 2: Searching Google Places...")
        google_results = self._search_google_places(city, neighborhoods, cuisine_type)

        # Step 3: Search web sources
        print(f"\n🌐 Step 3: Searching web sources...")
        web_pages = self._search_web(city, neighborhoods)

        # Step 4: Aggregate and deduplicate
        print(f"\n🤖 Step 4: Aggregating results...")
        restaurants = self._aggregate(google_results, web_pages, city, neighborhoods)

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

    @traceable(name="discover_neighborhoods")
    def _discover_neighborhoods(self, city: str) -> List[str]:
        """Discover food neighborhoods for the city."""
        return discover_neighborhoods.invoke({
            "city": city,
            "max_neighborhoods": 5
        })

    @traceable(name="search_google_places")
    def _search_google_places(
        self,
        city: str,
        neighborhoods: List[str],
        cuisine_type: str = None
    ) -> List[Dict]:
        """Search Google Places for restaurants."""
        return search_google_places.invoke({
            "city": city,
            "neighborhoods": neighborhoods,
            "cuisine_type": cuisine_type
        })

    @traceable(name="search_web")
    def _search_web(
        self,
        city: str,
        neighborhoods: List[str]
    ) -> List[str]:
        """Search web sources for restaurant recommendations."""
        return search_web_restaurants.invoke({
            "city": city,
            "neighborhoods": neighborhoods
        })

    @traceable(name="aggregate_results")
    def _aggregate(
        self,
        google_results: List[Dict],
        web_pages: List[str],
        city: str,
        neighborhoods: List[str]
    ) -> List[Dict]:
        """Aggregate and deduplicate all results."""
        return aggregate_restaurants.invoke({
            "google_places_results": google_results,
            "web_page_contents": web_pages,
            "city": city,
            "neighborhoods": neighborhoods
        })

    def _save_results(self, result: DiningResult):
        """Save results to a timestamped file."""
        # Create city folder
        city_folder = result.city.replace(" ", "_")
        output_path = Path(self.output_dir) / city_folder
        output_path.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}.json"
        filepath = output_path / filename

        # Save to file
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

    def format_results(self, result: DiningResult) -> str:
        """
        Format results for display.

        Args:
            result: DiningResult from run()

        Returns:
            Formatted string for printing
        """
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"🍽️  RESTAURANTS IN {result.city.upper()}")
        lines.append(f"{'='*60}")

        # Show neighborhoods
        if result.neighborhoods:
            lines.append(f"\n📍 NEIGHBORHOODS IDENTIFIED:")
            for hood in result.neighborhoods:
                lines.append(f"   • {hood}")
            lines.append("")

        for i, r in enumerate(result.restaurants, 1):
            name = r.get("name", "Unknown")
            rating = r.get("rating")
            reviews = r.get("review_count")
            price = r.get("price_level", "")
            cuisine = r.get("cuisine_type", "")
            neighborhood = r.get("neighborhood", "")
            source = r.get("source", "")

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


def run_dining_agent(
    city: str,
    cuisine_type: str = None,
    output_dir: str = None
) -> DiningResult:
    """
    Convenience function to run the dining agent.

    Args:
        city: City to search (e.g., "San Francisco")
        cuisine_type: Optional cuisine filter
        output_dir: Optional directory to save results

    Returns:
        DiningResult with all discovered restaurants
    """
    agent = DiningAgent(output_dir=output_dir)
    return agent.run(city, cuisine_type=cuisine_type)


if __name__ == "__main__":
    # Test the agent
    result = run_dining_agent("San Francisco")
    print(f"Found {result.total_restaurants} restaurants")
