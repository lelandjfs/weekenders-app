"""
LangChain Concert Agent
========================

Main concert discovery agent using LangChain patterns.
Orchestrates multiple tools for comprehensive concert coverage.

Features:
- Full LangSmith tracing for observability
- Modular tool-based architecture
- Automatic weekend date calculation
- Multi-source aggregation (Ticketmaster + Web)

Usage:
    from langchain_final import ConcertAgent

    agent = ConcertAgent()
    results = agent.run("San Francisco, CA", weekend="next")
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from langsmith import traceable

# Local imports
from .date_utils import get_concert_weekend_dates
from .config import setup_langsmith, MAX_VENUES_TO_DISCOVER
from .tools import (
    search_ticketmaster,
    search_web_concerts,
    discover_venues,
    aggregate_concert_results
)

# Import context router from parent directory
import sys
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Also add grandparent for context_router
_grandparent_dir = os.path.dirname(_parent_dir)
if _grandparent_dir not in sys.path:
    sys.path.insert(0, _grandparent_dir)

from context_router import analyze_city


@dataclass
class ConcertResult:
    """Structured result from concert agent."""
    location: str
    start_date: str
    end_date: str
    total_concerts: int
    concerts: List[Dict[str, Any]]
    sources: Dict[str, int]
    execution_time_seconds: float


class ConcertAgent:
    """
    LangChain-compatible concert discovery agent.

    Orchestrates multiple tools to find concerts:
    1. Analyzes city to get search parameters
    2. Searches Ticketmaster for mainstream concerts
    3. Discovers indie venues for the location
    4. Searches web sources for indie/small venue concerts
    5. Aggregates and deduplicates all results

    All operations are traced in LangSmith for observability.
    """

    def __init__(
        self,
        project_name: str = "weekenders-concert-agent",
        enable_tracing: bool = True,
        output_dir: str = None
    ):
        """
        Initialize the Concert Agent.

        Args:
            project_name: LangSmith project name for tracing
            enable_tracing: Whether to enable LangSmith tracing
            output_dir: Directory to save results (optional)
        """
        self.project_name = project_name
        self.enable_tracing = enable_tracing
        self.output_dir = output_dir

        # Setup LangSmith tracing
        setup_langsmith(project_name, enable_tracing)

    @traceable(name="concert_agent_run")
    def run(
        self,
        location: str,
        weekend: str = "next",
        start_date: str = None,
        end_date: str = None,
        save_results: bool = True
    ) -> ConcertResult:
        """
        Run the concert agent for a location.

        Args:
            location: City to search (e.g., "San Francisco, CA")
            weekend: "next" or "this" for automatic date calculation
            start_date: Override start date (YYYY-MM-DD)
            end_date: Override end date (YYYY-MM-DD)
            save_results: Whether to save results to disk

        Returns:
            ConcertResult with all discovered concerts
        """
        start_time = datetime.now()

        # Calculate dates if not provided
        if not start_date or not end_date:
            start_date, end_date = get_concert_weekend_dates(weekend)

        print(f"\n{'='*70}")
        print(f"🎸 CONCERT AGENT: {location}")
        print(f"{'='*70}")
        print(f"📅 Date Range: {start_date} to {end_date}")

        # Step 1: Get search context
        print(f"\n1️⃣  Analyzing location...")
        context = self._analyze_location(location, start_date, end_date)

        # Step 2: Search Ticketmaster
        print(f"\n2️⃣  Searching Ticketmaster...")
        ticketmaster_results = self._search_ticketmaster(context, start_date, end_date)
        print(f"   ✅ Found {len(ticketmaster_results)} concerts")

        # Step 3: Discover venues
        print(f"\n3️⃣  Discovering indie venues...")
        city = context.location_info.normalized_location.split(",")[0].strip()
        venues = self._discover_venues(city)
        print(f"   ✅ Found {len(venues)} venues: {', '.join(venues)}")

        # Step 4: Search web sources
        print(f"\n4️⃣  Searching web sources...")
        web_pages = self._search_web(city, start_date, end_date, venues)
        print(f"   ✅ Extracted {len(web_pages)} pages")

        # Step 5: Aggregate results
        print(f"\n5️⃣  Aggregating results...")
        final_concerts = self._aggregate(
            ticketmaster_results,
            web_pages,
            start_date,
            end_date,
            context.location_info.normalized_location
        )
        print(f"   ✅ {len(final_concerts)} unique concerts")

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Build result
        result = ConcertResult(
            location=context.location_info.normalized_location,
            start_date=start_date,
            end_date=end_date,
            total_concerts=len(final_concerts),
            concerts=final_concerts,
            sources={
                "ticketmaster": len(ticketmaster_results),
                "web_pages": len(web_pages),
                "venues_discovered": len(venues)
            },
            execution_time_seconds=execution_time
        )

        # Save results if requested
        if save_results and self.output_dir:
            self._save_results(result, location)

        # Print summary
        self._print_summary(result)

        return result

    @traceable(name="analyze_location")
    def _analyze_location(self, location: str, start_date: str, end_date: str):
        """Analyze location to get search parameters."""
        return analyze_city(location, start_date, end_date)

    @traceable(name="search_ticketmaster")
    def _search_ticketmaster(
        self,
        context,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """Search Ticketmaster for concerts."""
        return search_ticketmaster.invoke({
            "latitude": context.location_info.latitude,
            "longitude": context.location_info.longitude,
            "radius_miles": int(context.search_parameters.concert_radius_miles),
            "start_date": start_date,
            "end_date": end_date
        })

    @traceable(name="discover_venues")
    def _discover_venues(self, city: str) -> List[str]:
        """Discover indie venues for the city."""
        return discover_venues.invoke({
            "city": city,
            "max_venues": MAX_VENUES_TO_DISCOVER
        })

    @traceable(name="search_web")
    def _search_web(
        self,
        city: str,
        start_date: str,
        end_date: str,
        venues: List[str]
    ) -> List[str]:
        """Search web sources for concerts."""
        return search_web_concerts.invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "venues": venues
        })

    @traceable(name="aggregate_results")
    def _aggregate(
        self,
        ticketmaster_results: List[Dict],
        web_pages: List[str],
        start_date: str,
        end_date: str,
        location: str = ""
    ) -> List[Dict]:
        """Aggregate and deduplicate all results."""
        return aggregate_concert_results.invoke({
            "ticketmaster_results": ticketmaster_results,
            "web_page_contents": web_pages,
            "start_date": start_date,
            "end_date": end_date,
            "location": location
        })

    def _save_results(self, result: ConcertResult, location: str):
        """Save results to disk."""
        # Create output directory
        safe_location = location.replace(", ", "_").replace(" ", "_")
        date_range = f"{result.start_date}_to_{result.end_date}"
        output_path = Path(self.output_dir) / safe_location / date_range

        output_path.mkdir(parents=True, exist_ok=True)

        # Save results
        with open(output_path / "results.json", "w") as f:
            json.dump(asdict(result), f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")

    def _print_summary(self, result: ConcertResult):
        """Print a summary of results."""
        print(f"\n{'='*70}")
        print(f"✅ COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   Location: {result.location}")
        print(f"   Date Range: {result.start_date} to {result.end_date}")
        print(f"   Total Concerts: {result.total_concerts}")
        print(f"   Ticketmaster: {result.sources['ticketmaster']}")
        print(f"   Web Pages: {result.sources['web_pages']}")
        print(f"   Venues Discovered: {result.sources['venues_discovered']}")
        print(f"   Execution Time: {result.execution_time_seconds:.2f}s")

        if result.concerts:
            print(f"\n🎵 Sample Concerts (first 5):")
            for i, concert in enumerate(result.concerts[:5], 1):
                print(f"   {i}. {concert['name']}")
                print(f"      {concert['venue']} - {concert['date']}")
                print(f"      Source: {concert['source']}")

        print(f"\n{'='*70}\n")


def run_concert_agent(
    location: str,
    weekend: str = "next",
    output_dir: str = None
) -> ConcertResult:
    """
    Convenience function to run the concert agent.

    Args:
        location: City to search (e.g., "San Francisco, CA")
        weekend: "next" or "this" for automatic date calculation
        output_dir: Optional directory to save results

    Returns:
        ConcertResult with all discovered concerts
    """
    if output_dir is None:
        output_dir = str(Path(__file__).parent.parent / "test_results")

    agent = ConcertAgent(output_dir=output_dir)
    return agent.run(location, weekend)


if __name__ == "__main__":
    # Test the agent
    result = run_concert_agent("San Francisco, CA", "next")
    print(f"Found {result.total_concerts} concerts")
